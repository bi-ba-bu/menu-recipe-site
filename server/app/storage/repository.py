"""
storage/repository.py — 领域数据仓库

职责：把"文件存储"包装成面向业务的对象访问，
并提供与前端展示完全一致的数据结构。

存储策略（对应前端展示的信息）：

    前端展示               后端存储
    ─────────────────────  ─────────────────────────────────────
    菜品缩略图 / 名称 / 标签  recipes.json → id / name / tags
    时长 / 难度 / 份量        recipes.json → time / difficulty / serving
    营养拆解（5 项）          recipes.json → nutrition{calorie,protein,fat,carb,fiber}
    食材清单（主料标记）      recipes.json → ingredients[{name,amount,main}]
    烹饪步骤 + 每步耗时       recipes.json → steps[{title,desc,minutes}]
    小贴士                   recipes.json → tips
    一周菜单 / 点餐篮         orders.json  → 按「家庭」隔离（同家庭共享）
    我的收藏                 favorites.json → 按「用户」隔离
    登录用户                 users.json   → 账号、密码哈希
    登录会话                 sessions.json → token → userId
    吃住关系                 families.json → 家庭与其成员

隔离原则：
    · 菜单挂在 familyId 上 —— 同家庭成员的菜单一致
    · 收藏挂在 userId 上   —— 每个账号各自独立
    · 用户必属于某个家庭；单人注册时自动创建一个"默认家庭"
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .json_store import JsonStore

# ── 领域常量（与前端 order.js 保持一致） ─────────────────────────

DAYS: tuple[dict[str, str], ...] = (
    {"key": "mon", "label": "周一"},
    {"key": "tue", "label": "周二"},
    {"key": "wed", "label": "周三"},
    {"key": "thu", "label": "周四"},
    {"key": "fri", "label": "周五"},
    {"key": "sat", "label": "周六"},
    {"key": "sun", "label": "周日"},
)

MEALS: tuple[dict[str, str], ...] = (
    {"key": "breakfast", "label": "早餐"},
    {"key": "lunch", "label": "午餐"},
    {"key": "dinner", "label": "晚餐"},
)

DAY_KEYS = tuple(d["key"] for d in DAYS)
MEAL_KEYS = tuple(m["key"] for m in MEALS)

TAG_META: dict[str, dict[str, str]] = {
    "light": {"label": "清淡", "color": "success"},
    "meat": {"label": "荤菜", "color": "danger"},
    "veg": {"label": "素菜", "color": "success"},
    "soup": {"label": "汤羹", "color": "info"},
    "staple": {"label": "主食", "color": "warn"},
    "spicy": {"label": "辛辣", "color": "danger"},
    "quick": {"label": "快手", "color": "info"},
    "warming": {"label": "暖胃", "color": "warn"},
}

# ── 菜谱状态 ────────────────────────────────────────────────────
# public   公共菜谱：系统内置或审核通过，所有用户可见
# private  个人菜谱：仅创建者可见，未提交审核
# pending  待审核：创建者提交，等待管理员处理
# rejected 已驳回：审核未通过，仅创建者可见，可修改后重新提交
# archived 已下架：不再出现在点餐列表，但历史菜单仍可正常展示
RECIPE_STATUS_PUBLIC = "public"
RECIPE_STATUS_PRIVATE = "private"
RECIPE_STATUS_PENDING = "pending"
RECIPE_STATUS_REJECTED = "rejected"
RECIPE_STATUS_ARCHIVED = "archived"

RECIPE_STATUSES = (
    RECIPE_STATUS_PUBLIC,
    RECIPE_STATUS_PRIVATE,
    RECIPE_STATUS_PENDING,
    RECIPE_STATUS_REJECTED,
    RECIPE_STATUS_ARCHIVED,
)

STATUS_LABEL: dict[str, str] = {
    RECIPE_STATUS_PUBLIC: "公共",
    RECIPE_STATUS_PRIVATE: "个人",
    RECIPE_STATUS_PENDING: "待审核",
    RECIPE_STATUS_REJECTED: "已驳回",
    RECIPE_STATUS_ARCHIVED: "已下架",
}

# 系统账号 id：内置菜谱的归属
SYSTEM_OWNER = "system"

# 每日建议摄入量（营养完成度进度条的分母）
NUTRITION_TARGET: dict[str, float] = {
    "calorie": 2000,
    "protein": 75,
    "fat": 65,
    "carb": 275,
    "fiber": 25,
}

DEFAULT_CONFIG: dict[str, Any] = {
    "week": {"key": "2024-W43", "label": "第 1 周", "range": "10/20 - 10/26"},
    "nutritionTarget": dict(NUTRITION_TARGET),
    "water": {"current": 1500, "target": 2000},
    "weather": {"text": "22°C 多云"},
    # 审核员名单：菜谱审核权限只给这些用户名（首次启动写入配置，可在后台改）
    "reviewers": ["admin"],
}


def empty_week() -> dict[str, dict[str, list[dict[str, Any]]]]:
    """生成一个空周结构：7 天 × 3 餐，每餐为空数组。"""
    return {day: {meal: [] for meal in MEAL_KEYS} for day in DAY_KEYS}


def empty_orders() -> dict[str, Any]:
    """
    订单文件结构（按家庭隔离）：

        {
          "families": {
            "<familyId>": {
               "active": "<weekKey>",
               "weeks": { "<weekKey>": { "mon": {...}, ... } }
            }
          }
        }
    """
    return {"families": {}}


def empty_favorites() -> dict[str, Any]:
    """
    收藏文件结构（按用户隔离）：

        { "<userId>": ["dish-id", ...] }
    """
    return {}


def empty_users() -> dict[str, Any]:
    """
    用户文件结构：

        {
          "<userId>": {
             "id": "...", "username": "...", "displayName": "...",
             "passwordHash": "...", "salt": "...", "iterations": 200000,
             "familyId": "...", "createdAt": "..."
          }
        }
    """
    return {}


def empty_families() -> dict[str, Any]:
    """
    家庭文件结构（为后续「多账号绑定一个家庭」预留）：

        { "<familyId>": { "id", "name", "ownerId", "members": [userId], "createdAt" } }
    """
    return {}


def empty_sessions() -> dict[str, Any]:
    """
    会话文件结构：token → { "userId", "createdAt", "expiresAt" }
    """
    return {}


class Repository:
    """聚合全部存储文件的访问入口。"""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.recipes = JsonStore(self.data_dir / "recipes.json", dict)
        self.orders = JsonStore(self.data_dir / "orders.json", empty_orders)
        self.favorites = JsonStore(self.data_dir / "favorites.json", empty_favorites)
        self.users = JsonStore(self.data_dir / "users.json", empty_users)
        self.families = JsonStore(self.data_dir / "families.json", empty_families)
        self.sessions = JsonStore(self.data_dir / "sessions.json", empty_sessions)
        self.config = JsonStore(self.data_dir / "config.json", lambda: copy.deepcopy(DEFAULT_CONFIG))

    # ── 菜品库（只读为主） ──────────────────────────────────────

    def all_recipes(self) -> dict[str, Any]:
        return self.recipes.read()

    def get_recipe(self, dish_id: str) -> dict[str, Any] | None:
        return self.all_recipes().get(dish_id)

    def recipe_ids(self) -> list[str]:
        return list(self.all_recipes().keys())

    # ── 菜谱维护 ────────────────────────────────────────────────

    def save_recipe(self, dish_id: str, recipe: dict[str, Any]) -> dict[str, Any]:
        """新增或整体覆盖一条菜谱。"""

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(data, dict):
                data = {}
            data[dish_id] = recipe
            return data

        self.recipes.update(_mutate)
        return recipe

    def update_recipe(self, dish_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        """局部更新菜谱字段。"""
        result: dict[str, Any] = {}

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            recipe = data.get(dish_id)
            if isinstance(recipe, dict):
                recipe.update(changes)
                result.update(recipe)
            return data

        self.recipes.update(_mutate)
        return result or None

    def delete_recipe(self, dish_id: str) -> bool:
        """物理删除（仅用于个人菜谱且未被任何菜单引用时）。"""
        existed = {"v": False}

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            if dish_id in data:
                existed["v"] = True
                data.pop(dish_id, None)
            return data

        self.recipes.update(_mutate)
        return existed["v"]

    def is_recipe_used_by_any_family(self, dish_id: str) -> bool:
        """
        该菜谱是否仍被某个家庭的历史菜单引用。

        下架判断用：被引用的菜谱不能物理删除，否则历史菜单会显示失败。
        """
        orders = self.orders.read()
        for bucket in (orders.get("families") or {}).values():
            weeks = (bucket or {}).get("weeks") or {}
            for week in weeks.values():
                for day in (week or {}).values():
                    for items in (day or {}).values():
                        if not isinstance(items, list):
                            continue
                        if any(isinstance(it, dict) and it.get("id") == dish_id for it in items):
                            return True
        return False

    # ── 配置 ────────────────────────────────────────────────────

    def get_config(self) -> dict[str, Any]:
        cfg = self.config.read()
        # 兜底补齐缺失字段，避免旧文件缺 key 时接口报错
        merged = copy.deepcopy(DEFAULT_CONFIG)
        merged.update(cfg or {})
        return merged

    # ── 订单（按家庭隔离） ──────────────────────────────────────

    def _family_bucket(self, data: dict[str, Any], family_id: str) -> dict[str, Any]:
        """确保订单数据里存在指定家庭的分区。"""
        families = data.setdefault("families", {})
        bucket = families.get(family_id)
        if not isinstance(bucket, dict):
            bucket = {"active": None, "weeks": {}}
            families[family_id] = bucket
        bucket.setdefault("weeks", {})
        return bucket

    def active_week_key(self, family_id: str) -> str:
        """该家庭当前操作的是哪一周；未设置时用配置里的当前周。"""
        data = self.orders.read()
        bucket = (data.get("families") or {}).get(family_id) or {}
        active = bucket.get("active")
        return active or self.get_config()["week"]["key"]

    def get_week_orders(self, family_id: str, week_key: str | None = None) -> dict[str, Any]:
        """
        读取某家庭某一周的点餐数据。

        注意：同一家庭的成员共享这份数据，这是"同家庭菜单一致"的实现基础。
        """
        key = week_key or self.active_week_key(family_id)
        data = self.orders.read()
        families = data.get("families") or {}
        bucket = families.get(family_id) or {}
        weeks = bucket.get("weeks") or {}
        raw = weeks.get(key)
        if not isinstance(raw, dict):
            return empty_week()

        # 读时做结构校正，过滤无效菜品与非法数量
        valid_ids = set(self.recipe_ids())
        result = empty_week()
        for day in DAY_KEYS:
            day_data = raw.get(day)
            if not isinstance(day_data, dict):
                continue
            for meal in MEAL_KEYS:
                items = day_data.get(meal)
                if not isinstance(items, list):
                    continue
                cleaned = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    dish_id = item.get("id")
                    if dish_id not in valid_ids:
                        continue
                    try:
                        qty = int(item.get("qty", 1))
                    except (TypeError, ValueError):
                        qty = 1
                    cleaned.append({"id": dish_id, "qty": max(1, min(99, qty))})
                result[day][meal] = cleaned
        return result

    def save_week_orders(
        self, family_id: str, week: dict[str, Any], week_key: str | None = None
    ) -> None:
        """整体保存某家庭某一周的点餐数据。"""
        key = week_key or self.active_week_key(family_id)

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            bucket = self._family_bucket(data, family_id)
            bucket["weeks"][key] = week
            bucket["active"] = key
            return data

        self.orders.update(_mutate)

    # ── 收藏（按用户隔离） ──────────────────────────────────────

    def get_favorites(self, user_id: str) -> list[str]:
        data = self.favorites.read()
        raw = data.get(user_id) if isinstance(data, dict) else None
        if not isinstance(raw, list):
            return []
        valid = set(self.recipe_ids())
        # 去重并保持顺序，过滤已下架的菜品
        seen: set[str] = set()
        result: list[str] = []
        for item in raw:
            if isinstance(item, str) and item in valid and item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def set_favorites(self, user_id: str, ids: list[str]) -> list[str]:
        valid = set(self.recipe_ids())
        seen: set[str] = set()
        cleaned: list[str] = []
        for item in ids:
            if isinstance(item, str) and item in valid and item not in seen:
                seen.add(item)
                cleaned.append(item)

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(data, dict):
                data = {}
            data[user_id] = cleaned
            return data

        self.favorites.update(_mutate)
        return cleaned

    # ── 用户 ────────────────────────────────────────────────────

    def all_users(self) -> dict[str, Any]:
        data = self.users.read()
        return data if isinstance(data, dict) else {}

    def find_user_by_username(self, username: str) -> dict[str, Any] | None:
        """用户名大小写不敏感，避免 "Tom" 与 "tom" 注册成两个账号。"""
        target = username.strip().lower()
        for user in self.all_users().values():
            if isinstance(user, dict) and str(user.get("username", "")).lower() == target:
                return user
        return None

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        user = self.all_users().get(user_id)
        return user if isinstance(user, dict) else None

    def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(data, dict):
                data = {}
            data[user["id"]] = user
            return data

        self.users.update(_mutate)
        return user

    def update_user(self, user_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        """更新用户字段（如 lastFamilyId），返回更新后的对象。"""
        result: dict[str, Any] = {}

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            user = data.get(user_id)
            if isinstance(user, dict):
                user.update(changes)
                result.update(user)
            return data

        self.users.update(_mutate)
        return result or None

    # ── 家庭（多对多：一个用户可属于多个家庭） ──────────────────

    def all_families(self) -> dict[str, Any]:
        data = self.families.read()
        return data if isinstance(data, dict) else {}

    def get_family(self, family_id: str) -> dict[str, Any] | None:
        family = self.all_families().get(family_id)
        return family if isinstance(family, dict) else None

    def list_families_of_user(self, user_id: str) -> list[dict[str, Any]]:
        """该用户加入的全部家庭（含自己创建的家）。"""
        result = []
        for family in self.all_families().values():
            if not isinstance(family, dict):
                continue
            if user_id == family.get("ownerId") or user_id in (family.get("members") or []):
                result.append(family)
        # 自己当家长的家庭排在前面，便于切换器展示
        result.sort(key=lambda f: (0 if f.get("ownerId") == user_id else 1, f.get("createdAt", "")))
        return result

    def create_family(self, family: dict[str, Any]) -> dict[str, Any]:
        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(data, dict):
                data = {}
            data[family["id"]] = family
            return data

        self.families.update(_mutate)
        return family

    def update_family(self, family_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        """更新家庭字段（名称、邀请码等），返回更新后的对象。"""

        result: dict[str, Any] = {}

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            family = data.get(family_id)
            if isinstance(family, dict):
                family.update(changes)
                result.update(family)
            return data

        self.families.update(_mutate)
        return result or None

    def add_family_member(self, family_id: str, user_id: str) -> None:
        """把用户加入家庭成员列表（不重复添加）。"""

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            family = data.get(family_id)
            if isinstance(family, dict):
                members = family.setdefault("members", [])
                if user_id not in members:
                    members.append(user_id)
            return data

        self.families.update(_mutate)

    def remove_family_member(self, family_id: str, user_id: str) -> None:
        """把用户移出家庭成员列表（不影响其自建家庭）。"""

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            family = data.get(family_id)
            if isinstance(family, dict):
                members = family.get("members") or []
                if user_id in members:
                    family["members"] = [m for m in members if m != user_id]
            return data

        self.families.update(_mutate)

    def find_family_by_invite_code(self, code: str) -> dict[str, Any] | None:
        """按邀请码查家庭（大小写不敏感）。"""
        target = (code or "").strip().upper()
        if not target:
            return None
        for family in self.all_families().values():
            if isinstance(family, dict) and str(family.get("inviteCode", "")).upper() == target:
                return family
        return None

    def delete_family(self, family_id: str) -> None:
        """删除家庭（家长解散时用），同时清理该家庭的菜单数据。"""

        def _mutate_families(data: dict[str, Any]) -> dict[str, Any]:
            if isinstance(data, dict):
                data.pop(family_id, None)
            return data

        self.families.update(_mutate_families)

        def _mutate_orders(data: dict[str, Any]) -> dict[str, Any]:
            if isinstance(data, dict):
                (data.get("families") or {}).pop(family_id, None)
            return data

        self.orders.update(_mutate_orders)

    # ── 会话 ────────────────────────────────────────────────────

    def save_session(self, token: str, session: dict[str, Any]) -> None:
        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(data, dict):
                data = {}
            data[token] = session
            return data

        self.sessions.update(_mutate)

    def get_session(self, token: str) -> dict[str, Any] | None:
        data = self.sessions.read()
        session = data.get(token) if isinstance(data, dict) else None
        return session if isinstance(session, dict) else None

    def update_session(self, token: str, changes: dict[str, Any]) -> None:
        """更新会话（如切换家庭时记录 currentFamilyId）。"""

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            session = data.get(token)
            if isinstance(session, dict):
                session.update(changes)
            return data

        self.sessions.update(_mutate)

    def delete_session(self, token: str) -> None:
        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            if isinstance(data, dict):
                data.pop(token, None)
            return data

        self.sessions.update(_mutate)

    def purge_expired_sessions(self, now_iso: str) -> int:
        """清理过期会话，避免文件无限增长。返回清理条数。"""

        removed = {"n": 0}

        def _mutate(data: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(data, dict):
                return {}
            keep = {
                token: sess
                for token, sess in data.items()
                if isinstance(sess, dict) and str(sess.get("expiresAt", "")) > now_iso
            }
            removed["n"] = len(data) - len(keep)
            return keep

        self.sessions.update(_mutate)
        return removed["n"]
