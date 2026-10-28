"""
services/recipe_service.py — 菜谱维护与审核服务

对应前端展示：
    · 我的菜谱页（个人/待审核/已驳回/已下架 + 公共只读）
    · 菜谱编辑弹窗（新增 / 修改）
    · 审核页（待审核列表、通过 / 驳回）

菜谱归属与状态模型（与 repository.py 的常量一一对应）：

    ownerId                 status        谁能看到              谁能改
    ──────────────────────  ────────────  ────────────────────  ──────────────────
    system（内置菜谱）        public        所有人                谁都不能改
    普通用户                 private       仅创建者              创建者
    普通用户                 pending       仅创建者（等待审核）    创建者（可撤回）
    普通用户                 rejected      仅创建者              创建者（改后可重提）
    普通用户                 archived      仅创建者              创建者（可恢复）

    审核通过后 status 变 public 且 ownerId 仍是原创建者，
    因此"公共"≠"系统所有"：判断可编辑性要看 status，不能只看 ownerId。

权限判定（为什么放在服务层而不是 router）：
    前端需要在列表里直接拿到 canEdit / canSubmit / canReview 三个布尔值来渲染按钮，
    把这些判定集中在 _view() 里，保证"后端说了算"与"前端显示"永远一致。
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from ..storage.repository import (
    RECIPE_STATUS_ARCHIVED,
    RECIPE_STATUS_PENDING,
    RECIPE_STATUS_PRIVATE,
    RECIPE_STATUS_PUBLIC,
    RECIPE_STATUS_REJECTED,
    STATUS_LABEL,
    SYSTEM_OWNER,
    TAG_META,
    Repository,
)


class RecipeError(Exception):
    """菜谱业务异常，message 可直接展示给用户。"""


class RecipeNotFound(RecipeError):
    """菜谱不存在（router 会转成 404）。"""


class RecipeForbidden(RecipeError):
    """无权操作（router 会转成 403）。"""


# ── 字段约束 ────────────────────────────────────────────────────

MAX_NAME_LEN = 30
MAX_SUBTITLE_LEN = 60
MAX_DESC_LEN = 500
MAX_SERVING_LEN = 20
MAX_TIPS_LEN = 500
MAX_INGREDIENTS = 50
MAX_STEPS = 30
MAX_MINUTES = 1440
# 难度取值与前端下拉框保持一致
DIFFICULTIES = ("简单", "中等", "进阶")
DIFFICULTY_DEFAULT = "中等"
# 营养五项（热量 + 四大营养素）
NUTRITION_KEYS = ("calorie", "protein", "fat", "carb", "fiber")

# 列表 / 详情里对外暴露的字段（白名单，避免把内部字段传出去）
_PASSTHROUGH_FIELDS = (
    "name",
    "subtitle",
    "desc",
    "cover",
    "emoji",
    "time",
    "difficulty",
    "serving",
    "tags",
    "nutrition",
    "ingredients",
    "steps",
    "tips",
)

# 允许通过 PATCH 修改的字段
_EDITABLE_FIELDS = _PASSTHROUGH_FIELDS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, limit: int | None = None) -> str:
    """把任意输入规整成字符串；非字符串一律当作空串，避免把对象塞进 JSON。"""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if limit is not None:
        value = value[:limit]
    return value


def _number(value: Any, default: float = 0.0) -> float:
    """宽松数值解析：非法输入回落默认值，负数截断为 0。"""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    if num != num or num in (float("inf"), float("-inf")):  # NaN / inf
        return default
    return max(0.0, num)


def _clean_nutrition(raw: Any, base: dict[str, Any] | None = None) -> dict[str, Any]:
    """营养五项：缺失的键沿用 base（修改时），否则取 0。"""
    source = raw if isinstance(raw, dict) else {}
    base = base or {}
    result: dict[str, Any] = {}
    for key in NUTRITION_KEYS:
        value = _number(source.get(key, base.get(key, 0)))
        # 热量取整，营养素保留一位小数（与种子数据风格一致）
        result[key] = int(round(value)) if key == "calorie" else round(value, 1)
    return result


def _clean_ingredients(raw: Any) -> list[dict[str, Any]]:
    """食材列表：过滤空行，最多 MAX_INGREDIENTS 条。"""
    if not isinstance(raw, list):
        return []
    items: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name = _text(entry.get("name"), 50)
        if not name:
            continue
        items.append(
            {
                "name": name,
                "amount": _text(entry.get("amount"), 30),
                "main": bool(entry.get("main")),
            }
        )
        if len(items) >= MAX_INGREDIENTS:
            break
    return items


def _clean_steps(raw: Any) -> list[dict[str, Any]]:
    """步骤列表：标题与说明都为空的行丢弃，最多 MAX_STEPS 步。"""
    if not isinstance(raw, list):
        return []
    steps: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        title = _text(entry.get("title"), 60)
        desc = _text(entry.get("desc"), 500)
        if not title and not desc:
            continue
        steps.append(
            {
                "title": title or f"步骤 {len(steps) + 1}",
                "desc": desc,
                "minutes": int(min(MAX_MINUTES, _number(entry.get("minutes")))),
            }
        )
        if len(steps) >= MAX_STEPS:
            break
    return steps


def _clean_tags(raw: Any) -> list[str]:
    """标签：只保留 TAG_META 内的合法值，去重且保持原顺序。"""
    if isinstance(raw, str):
        candidates: list[Any] = [raw]
    elif isinstance(raw, list):
        candidates = raw
    else:
        candidates = []

    result: list[str] = []
    for item in candidates:
        key = _text(item)
        if key in TAG_META and key not in result:
            result.append(key)
    return result


class RecipeService:
    """菜谱的增删改查、状态流转与审核。"""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    # ── 权限判定 ────────────────────────────────────────────────

    def is_reviewer(self, user: dict[str, Any] | None) -> bool:
        """
        审核员判定：用户名出现在 config["reviewers"] 里。

        用户名大小写不敏感（与登录逻辑一致），配置缺省时回落到默认名单。
        """
        if not isinstance(user, dict):
            return False
        username = str(user.get("username", "")).strip().lower()
        if not username:
            return False
        raw = self.repo.get_config().get("reviewers")
        reviewers = raw if isinstance(raw, list) else []
        return username in {str(r).strip().lower() for r in reviewers}

    def _require_reviewer(self, user: dict[str, Any]) -> None:
        if not self.is_reviewer(user):
            raise RecipeForbidden("只有审核员可以进行审核操作")

    @staticmethod
    def _is_owner(recipe: dict[str, Any], user_id: str) -> bool:
        """是否为该菜谱的创建者（系统内置菜谱的"创建者"是 system，普通用户永远不是）。"""
        owner = recipe.get("ownerId") or (SYSTEM_OWNER if recipe.get("origin") == "seed" else "")
        if not owner or owner == SYSTEM_OWNER:
            return False
        return bool(user_id) and owner == user_id

    @staticmethod
    def _status_of(recipe: dict[str, Any]) -> str:
        """老数据没有 status 字段时视为公共菜谱（v1 的菜谱都是内置的）。"""
        status = recipe.get("status")
        return status if status in STATUS_LABEL else RECIPE_STATUS_PUBLIC

    def can_edit(self, recipe: dict[str, Any], user_id: str) -> bool:
        """
        可编辑 = 自己创建的，且状态允许修改。

        两种状态被排除在外：
            · public   审核通过的菜谱是公共资产，创建者也不能改，
                       否则会绕过审核流程直接影响所有用户的点餐橱窗
            · pending  已经提交审核，审核员正在看的那一版不能被作者改动，
                       否则会出现"审核员看到的与作者改后的不是同一份"
        想改 pending 的菜谱，先撤回（withdraw）。
        """
        if self._status_of(recipe) in (RECIPE_STATUS_PUBLIC, RECIPE_STATUS_PENDING):
            return False
        return self._is_owner(recipe, user_id)

    def can_submit(self, recipe: dict[str, Any], user_id: str) -> bool:
        """私人 / 已驳回的菜谱可以提交审核。"""
        return self._is_owner(recipe, user_id) and self._status_of(recipe) in (
            RECIPE_STATUS_PRIVATE,
            RECIPE_STATUS_REJECTED,
        )

    def can_withdraw(self, recipe: dict[str, Any], user_id: str) -> bool:
        """待审核中的菜谱可以撤回。"""
        return self._is_owner(recipe, user_id) and self._status_of(recipe) == RECIPE_STATUS_PENDING

    def can_archive(self, recipe: dict[str, Any], user_id: str) -> bool:
        """已下架的不能再下架。"""
        return self.can_edit(recipe, user_id) and self._status_of(recipe) != RECIPE_STATUS_ARCHIVED

    def can_restore(self, recipe: dict[str, Any], user_id: str) -> bool:
        """只有已下架的菜谱可以恢复。"""
        return self._is_owner(recipe, user_id) and self._status_of(recipe) == RECIPE_STATUS_ARCHIVED

    def can_delete(self, recipe: dict[str, Any], user_id: str) -> bool:
        """
        可物理删除 = 自己创建的，且不是公共 / 待审核菜谱。

        待审核的菜谱要先撤回再删，避免审核员正在处理的条目凭空消失。
        """
        if self._status_of(recipe) in (RECIPE_STATUS_PUBLIC, RECIPE_STATUS_PENDING):
            return False
        return self._is_owner(recipe, user_id)

    # ── 可见性 ──────────────────────────────────────────────────

    def is_visible(self, recipe: dict[str, Any], user_id: str) -> bool:
        """
        该菜谱对指定用户是否可见。

        public（未下架）所有人可见；其余状态只有创建者自己可见。
        """
        status = self._status_of(recipe)
        if status == RECIPE_STATUS_PUBLIC:
            return True
        return self._is_owner(recipe, user_id)

    def visible_recipes(self, user_id: str) -> list[tuple[str, dict[str, Any]]]:
        """
        当前用户可见的菜谱原表 (id, recipe)，供点餐橱窗等场景复用。

        规则与 is_visible 一致，但额外剔除已下架菜谱：
        已下架的菜谱不再出现在任何"可选菜"的列表里，
        只有历史菜单按 id 直接读取时才会展示。
        """
        result: list[tuple[str, dict[str, Any]]] = []
        for dish_id, recipe in self.repo.all_recipes().items():
            if not isinstance(recipe, dict):
                continue
            if self._status_of(recipe) == RECIPE_STATUS_ARCHIVED:
                continue
            if self.is_visible(recipe, user_id):
                result.append((dish_id, recipe))
        return result

    def _require_visible(self, dish_id: str, user: dict[str, Any]) -> dict[str, Any]:
        """
        取菜谱并校验可见性（用于"读"操作）。

        对无权查看的菜谱统一按"不存在"处理（404），
        避免用状态码差异探测别人的私人菜谱 id 是否存在。
        """
        recipe = self.repo.get_recipe(dish_id)
        if recipe is None or not self.is_visible(recipe, user.get("id", "")):
            raise RecipeNotFound(f"菜谱不存在：{dish_id}")
        return recipe

    def _require_writable(self, dish_id: str, user: dict[str, Any]) -> dict[str, Any]:
        """
        取菜谱并校验可见性（用于"写"操作）。

        与 _require_visible 的区别：菜谱确实存在、只是当前用户无权操作时返回 403 而不是 404。
        写操作本来就带有明确的意图（改/删/提交），给前端一个"这是别人的菜谱"的明确提示
        比伪装成不存在更有用；真正的存在性探测风险主要来自批量读接口，那边仍用 404。
        """
        recipe = self.repo.get_recipe(dish_id)
        if recipe is None:
            raise RecipeNotFound(f"菜谱不存在：{dish_id}")
        if not self.is_visible(recipe, user.get("id", "")):
            raise RecipeForbidden("无权操作该菜谱")
        return recipe

    # ── 视图 ────────────────────────────────────────────────────

    def _view(
        self, dish_id: str, recipe: dict[str, Any], user: dict[str, Any], detail: bool = False
    ) -> dict[str, Any]:
        """把存储结构转换为前端可直接渲染的菜谱视图。"""
        user_id = user.get("id", "")
        status = self._status_of(recipe)
        owner_id = recipe.get("ownerId") or (SYSTEM_OWNER if recipe.get("origin") == "seed" else "")
        owner = self.repo.get_user(owner_id) or {}
        nutrition = _clean_nutrition(recipe.get("nutrition"))
        tags = _clean_tags(recipe.get("tags"))

        data: dict[str, Any] = {
            "id": dish_id,
            "name": recipe.get("name", ""),
            "subtitle": recipe.get("subtitle", ""),
            "desc": recipe.get("desc", ""),
            "time": recipe.get("time", 0),
            "difficulty": recipe.get("difficulty", ""),
            "serving": recipe.get("serving", ""),
            "tags": tags,
            "calorie": nutrition["calorie"],
            "nutrition": nutrition,
            "status": status,
            "statusLabel": STATUS_LABEL.get(status, ""),
            "ownerId": owner_id,
            "ownerName": (
                "系统" if owner_id == SYSTEM_OWNER else (owner.get("displayName") or owner.get("username") or "")
            ),
            "origin": recipe.get("origin", ""),
            "isMine": self._is_owner(recipe, user_id),
            "isPublic": status == RECIPE_STATUS_PUBLIC,
            "reviewNote": recipe.get("reviewNote", "") or "",
            "submittedAt": recipe.get("submittedAt", "") or "",
            "createdAt": recipe.get("createdAt", ""),
            "updatedAt": recipe.get("updatedAt", ""),
            # 按钮显示与否完全由后端决定，前端不用再自己算权限
            "canEdit": self.can_edit(recipe, user_id),
            "canSubmit": self.can_submit(recipe, user_id),
            "canWithdraw": self.can_withdraw(recipe, user_id),
            "canArchive": self.can_archive(recipe, user_id),
            "canRestore": self.can_restore(recipe, user_id),
            "canDelete": self.can_delete(recipe, user_id),
            # 待审核状态 + 当前用户是审核员 + 不是自己的菜 → 显示通过/驳回按钮
            "canReview": (
                status == RECIPE_STATUS_PENDING
                and self.is_reviewer(user)
                and not self._is_owner(recipe, user_id)
            ),
            "tagMeta": [{"key": t, **TAG_META[t]} for t in tags],
        }

        if detail:
            # 详情页额外的展示字段
            steps = recipe.get("steps") or []
            data["cover"] = recipe.get("cover", "")
            data["emoji"] = recipe.get("emoji", "")
            data["ingredients"] = recipe.get("ingredients") or []
            data["steps"] = steps
            data["tips"] = recipe.get("tips", "")
            data["stepCount"] = len(steps)
            data["stepsTotalMinutes"] = sum(
                int(_number(s.get("minutes"))) for s in steps if isinstance(s, dict)
            )
            data["isFavorite"] = dish_id in self.repo.get_favorites(user_id)

        return data

    # ── 查询 ────────────────────────────────────────────────────

    def list_visible(self, user: dict[str, Any], include_own: bool = True) -> dict[str, Any]:
        """
        用户可见的菜谱 = 全部公共菜谱 + 自己的全部菜谱。

        include_own=False 时只返回公共菜谱（用于"只看官方"这类场景）。
        排序：自己的排前面（按更新时间倒序），公共菜谱按名称。
        """
        user_id = user.get("id", "")
        mine: list[dict[str, Any]] = []
        public: list[dict[str, Any]] = []

        for dish_id, recipe in self.repo.all_recipes().items():
            if not isinstance(recipe, dict):
                continue
            status = self._status_of(recipe)
            if self._is_owner(recipe, user_id):
                if include_own:
                    mine.append(self._view(dish_id, recipe, user))
                continue
            if status == RECIPE_STATUS_PUBLIC:
                public.append(self._view(dish_id, recipe, user))

        # 自己的菜单：待审核 > 已驳回 > 个人 > 已下架，同级按更新时间倒序
        weight = {
            RECIPE_STATUS_PENDING: 0,
            RECIPE_STATUS_REJECTED: 1,
            RECIPE_STATUS_PRIVATE: 2,
            RECIPE_STATUS_ARCHIVED: 3,
            RECIPE_STATUS_PUBLIC: 4,
        }
        mine.sort(key=lambda v: (weight.get(v["status"], 9), _neg_time(v.get("updatedAt"))))
        public.sort(key=lambda v: v.get("name", ""))

        items = mine + public
        counts = {
            "total": len(items),
            "mine": len(mine),
            "public": len(public),
            "private": sum(1 for v in mine if v["status"] == RECIPE_STATUS_PRIVATE),
            "pending": sum(1 for v in mine if v["status"] == RECIPE_STATUS_PENDING),
            "rejected": sum(1 for v in mine if v["status"] == RECIPE_STATUS_REJECTED),
            "archived": sum(1 for v in mine if v["status"] == RECIPE_STATUS_ARCHIVED),
        }
        return {
            "items": items,
            "total": len(items),
            "counts": counts,
            "isReviewer": self.is_reviewer(user),
        }

    def get(self, user: dict[str, Any], dish_id: str) -> dict[str, Any]:
        """菜谱详情（可见性受限）。"""
        recipe = self._require_visible(dish_id, user)
        return self._view(dish_id, recipe, user, detail=True)

    def list_pending(self, user: dict[str, Any]) -> dict[str, Any]:
        """待审核列表（仅审核员）。按提交时间正序，先提交的先处理。"""
        self._require_reviewer(user)
        items: list[dict[str, Any]] = []
        for dish_id, recipe in self.repo.all_recipes().items():
            if not isinstance(recipe, dict):
                continue
            if self._status_of(recipe) != RECIPE_STATUS_PENDING:
                continue
            view = self._view(dish_id, recipe, user, detail=True)
            items.append(view)

        items.sort(key=lambda v: v.get("submittedAt") or v.get("updatedAt") or "")
        return {
            "items": items,
            "total": len(items),
            "isReviewer": True,
            "reviewers": self.repo.get_config().get("reviewers") or [],
        }

    # ── 校验 ────────────────────────────────────────────────────

    def _normalize(
        self, payload: dict[str, Any], base: dict[str, Any] | None = None, *, partial: bool = False
    ) -> dict[str, Any]:
        """
        把请求体规整成完整的菜谱字段。

        base    修改时的原菜谱，未提交的字段沿用原值
        partial True 时只校验"提交了的字段"，用于 PATCH
        """
        if not isinstance(payload, dict):
            raise RecipeError("请求体必须是 JSON 对象")
        base = base or {}

        def pick(field: str) -> Any:
            return payload[field] if field in payload else base.get(field)

        result: dict[str, Any] = {}

        # 名称：必填 1-30 字
        name_raw = pick("name")
        name = _text(name_raw)
        if not name:
            raise RecipeError("菜谱名称不能为空")
        if len(name) > MAX_NAME_LEN:
            raise RecipeError(f"菜谱名称最多 {MAX_NAME_LEN} 个字")
        result["name"] = name

        # 时长：正整数分钟（新建必填；PATCH 未提交该字段时沿用原值）
        time_raw = pick("time")
        if time_raw is None or time_raw == "":
            if not partial or "time" in payload:
                raise RecipeError("请填写烹饪时长（分钟）")
            result["time"] = int(_number(base.get("time")))
        else:
            minutes = _number(time_raw)
            if minutes <= 0:
                raise RecipeError("烹饪时长必须是大于 0 的整数")
            result["time"] = int(min(MAX_MINUTES, round(minutes)))

        result["subtitle"] = _text(pick("subtitle"), MAX_SUBTITLE_LEN)
        result["desc"] = _text(pick("desc"), MAX_DESC_LEN)
        result["serving"] = _text(pick("serving"), MAX_SERVING_LEN)

        difficulty = _text(pick("difficulty"))
        if not difficulty:
            difficulty = DIFFICULTY_DEFAULT
        if difficulty not in DIFFICULTIES:
            raise RecipeError(f"难度只能是：{' / '.join(DIFFICULTIES)}")
        result["difficulty"] = difficulty

        result["tags"] = _clean_tags(pick("tags"))
        result["nutrition"] = _clean_nutrition(pick("nutrition"), base.get("nutrition"))
        result["ingredients"] = _clean_ingredients(pick("ingredients"))
        result["steps"] = _clean_steps(pick("steps"))
        result["tips"] = _text(pick("tips"), MAX_TIPS_LEN)

        # 食材与步骤：新建时必须至少各 1 项；修改时提交了才校验
        if result["ingredients"] == [] and (not partial or "ingredients" in payload):
            raise RecipeError("至少需要 1 项食材")
        if result["steps"] == [] and (not partial or "steps" in payload):
            raise RecipeError("至少需要 1 个烹饪步骤")

        # 封面与图标：前端不填时自动生成，保证卡片有东西可渲染。
        # 修改时若已提交的字段里不含 cover/emoji，就沿用原值，不重新生成。
        cover = _text(pick("cover"), 200)
        result["cover"] = cover or _default_cover(result["name"])
        emoji = _text(pick("emoji"), 8)
        result["emoji"] = emoji or _default_emoji(result["tags"])

        return result

    # ── 写入 ────────────────────────────────────────────────────

    def create(self, user: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        """新增个人菜谱：归属本人，状态为 private，需要审核才能变公共。"""
        user_id = user.get("id", "")
        if not user_id:
            raise RecipeForbidden("请先登录")

        fields = self._normalize(payload)
        dish_id = self._new_id()
        now = _now()

        recipe = {
            **fields,
            "id": dish_id,
            "ownerId": user_id,
            "status": RECIPE_STATUS_PRIVATE,
            "origin": "user",
            "reviewNote": "",
            "reviewedBy": "",
            "reviewedAt": "",
            "submittedAt": "",
            "createdAt": now,
            "updatedAt": now,
        }
        self.repo.save_recipe(dish_id, recipe)
        return self._view(dish_id, recipe, user, detail=True)

    def update(self, user: dict[str, Any], dish_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        修改菜谱：仅创建者、且状态允许修改。

        受限的两种情况：
            · public   审核通过或系统内置，任何人都不能改，否则等于绕过审核直接影响全站
            · pending  审核中，先撤回再改，避免审核员看到的内容与最终内容不一致
        """
        recipe = self._require_writable(dish_id, user)
        user_id = user.get("id", "")
        status = self._status_of(recipe)

        if status == RECIPE_STATUS_PUBLIC:
            raise RecipeForbidden("公共菜谱不可修改，请新增一份自己的菜谱")
        if not self._is_owner(recipe, user_id):
            raise RecipeForbidden("只能修改自己创建的菜谱")
        if status == RECIPE_STATUS_PENDING:
            raise RecipeForbidden("审核中的菜谱不能修改，请先撤回审核")

        fields = self._normalize(payload, recipe, partial=True)
        changes: dict[str, Any] = {f: fields[f] for f in _EDITABLE_FIELDS if f in fields}
        changes["updatedAt"] = _now()

        # 已驳回的菜谱修改后，清掉上次的驳回原因，避免误解
        if status == RECIPE_STATUS_REJECTED:
            changes["reviewNote"] = ""

        updated = self.repo.update_recipe(dish_id, changes) or {**recipe, **changes}
        return self._view(dish_id, updated, user, detail=True)

    def archive(self, user: dict[str, Any], dish_id: str) -> dict[str, Any]:
        """
        下架（软删除）：只改状态，不动数据。

        下架后不再出现在点餐橱窗，但历史菜单仍能正常展示——
        因为菜单条目按 id 引用菜谱，菜谱还在文件里。
        """
        recipe = self._require_writable(dish_id, user)
        if not self._is_owner(recipe, user.get("id", "")):
            raise RecipeForbidden("只能下架自己创建的菜谱")
        if self._status_of(recipe) == RECIPE_STATUS_PUBLIC:
            raise RecipeForbidden("公共菜谱不可下架")
        if self._status_of(recipe) == RECIPE_STATUS_ARCHIVED:
            raise RecipeError("该菜谱已经是下架状态")

        updated = (
            self.repo.update_recipe(
                dish_id, {"status": RECIPE_STATUS_ARCHIVED, "updatedAt": _now()}
            )
            or recipe
        )
        return self._view(dish_id, updated, user, detail=True)

    def restore(self, user: dict[str, Any], dish_id: str) -> dict[str, Any]:
        """恢复下架菜谱：回到 private（即使审核过的也降级为私人，公共身份需要重新审核）。"""
        recipe = self._require_writable(dish_id, user)
        if not self._is_owner(recipe, user.get("id", "")):
            raise RecipeForbidden("只能恢复自己创建的菜谱")
        if self._status_of(recipe) != RECIPE_STATUS_ARCHIVED:
            raise RecipeError("只有已下架的菜谱可以恢复")

        updated = (
            self.repo.update_recipe(
                dish_id, {"status": RECIPE_STATUS_PRIVATE, "updatedAt": _now()}
            )
            or recipe
        )
        return self._view(dish_id, updated, user, detail=True)

    def submit_review(self, user: dict[str, Any], dish_id: str) -> dict[str, Any]:
        """提交审核：private / rejected → pending。"""
        recipe = self._require_writable(dish_id, user)
        if not self._is_owner(recipe, user.get("id", "")):
            raise RecipeForbidden("只能提交自己创建的菜谱")
        if self._status_of(recipe) not in (RECIPE_STATUS_PRIVATE, RECIPE_STATUS_REJECTED):
            raise RecipeError("只有个人菜谱或已驳回的菜谱可以提交审核")

        now = _now()
        updated = (
            self.repo.update_recipe(
                dish_id,
                {
                    "status": RECIPE_STATUS_PENDING,
                    "submittedAt": now,
                    "updatedAt": now,
                    "reviewNote": "",
                },
            )
            or recipe
        )
        return self._view(dish_id, updated, user, detail=True)

    def withdraw_review(self, user: dict[str, Any], dish_id: str) -> dict[str, Any]:
        """撤回审核：pending → private。"""
        recipe = self._require_writable(dish_id, user)
        if not self._is_owner(recipe, user.get("id", "")):
            raise RecipeForbidden("只能撤回自己提交的菜谱")
        if self._status_of(recipe) != RECIPE_STATUS_PENDING:
            raise RecipeError("只有待审核的菜谱可以撤回")

        updated = (
            self.repo.update_recipe(
                dish_id,
                {"status": RECIPE_STATUS_PRIVATE, "submittedAt": "", "updatedAt": _now()},
            )
            or recipe
        )
        return self._view(dish_id, updated, user, detail=True)

    def review(
        self, reviewer: dict[str, Any], dish_id: str, approve: bool, note: str = ""
    ) -> dict[str, Any]:
        """
        审核：通过 → public（ownerId 保留原创建者），驳回 → rejected 并记录原因。

        审核员对自己的菜谱同样走这个流程（不允许自己审自己），
        避免"审核员顺手把自己的菜推成公共"。
        """
        self._require_reviewer(reviewer)

        recipe = self.repo.get_recipe(dish_id)
        if recipe is None:
            raise RecipeNotFound(f"菜谱不存在：{dish_id}")
        if self._status_of(recipe) != RECIPE_STATUS_PENDING:
            raise RecipeError("该菜谱不在待审核状态")
        if self._is_owner(recipe, reviewer.get("id", "")):
            raise RecipeForbidden("不能审核自己提交的菜谱")

        reason = _text(note, 200)
        if not approve and not reason:
            raise RecipeError("驳回时必须填写原因")

        now = _now()
        changes: dict[str, Any] = {
            "status": RECIPE_STATUS_PUBLIC if approve else RECIPE_STATUS_REJECTED,
            "reviewNote": "" if approve else reason,
            "reviewedBy": reviewer.get("id", ""),
            "reviewedAt": now,
            "updatedAt": now,
        }
        updated = self.repo.update_recipe(dish_id, changes) or recipe
        return self._view(dish_id, updated, reviewer, detail=True)

    def delete(self, user: dict[str, Any], dish_id: str) -> dict[str, Any]:
        """
        物理删除（DELETE /api/recipes/{id}）。

        拦截条件（任一命中即拒绝）：
            · 被任何家庭的历史菜单引用 —— 否则那些菜单会显示成空条目
            · 公共 / 待审核状态           —— 公共是共享资产，待审核中不该被删
            · 不是自己创建的              —— 越权
        其余情况先软下架再物理删除，语义与 handle cleanup 一致。
        """
        recipe = self._require_writable(dish_id, user)
        user_id = user.get("id", "")

        if not self._is_owner(recipe, user_id):
            raise RecipeForbidden("只能删除自己创建的菜谱")
        if self._status_of(recipe) == RECIPE_STATUS_PUBLIC:
            raise RecipeForbidden("公共菜谱不可删除")
        if self._status_of(recipe) == RECIPE_STATUS_PENDING:
            raise RecipeError("待审核的菜谱请先撤回，再删除")
        if self.repo.is_recipe_used_by_any_family(dish_id):
            raise RecipeError("该菜谱已被家庭菜单引用，不能删除；请使用下架")

        removed = self.repo.delete_recipe(dish_id)
        if not removed:
            raise RecipeNotFound(f"菜谱不存在：{dish_id}")
        # 顺手从各用户收藏里摘掉，避免收藏页出现空卡片
        self._purge_from_favorites(dish_id)
        return {"deleted": True, "id": dish_id}

    # ── 内部工具 ────────────────────────────────────────────────

    def _new_id(self) -> str:
        """r_<12 位 hex>，与 u_/f_ 前缀风格一致，且与内置菜谱的 slug id 不会冲突。"""
        for _ in range(20):
            candidate = f"r_{secrets.token_hex(6)}"
            if self.repo.get_recipe(candidate) is None:
                return candidate
        # 极端情况：退化为 uuid（几乎不可能命中）
        return f"r_{uuid.uuid4().hex[:12]}"

    def _purge_from_favorites(self, dish_id: str) -> None:
        """从所有用户的收藏里移除某个菜谱。"""
        data = self.repo.favorites.read()
        if not isinstance(data, dict):
            return
        dirty = False
        for user_id, ids in list(data.items()):
            if isinstance(ids, list) and dish_id in ids:
                data[user_id] = [i for i in ids if i != dish_id]
                dirty = True
        if dirty:
            self.repo.favorites.write(data)


def _neg_time(value: Any) -> float:
    """
    让"更新时间倒序"可以用升序排序实现。

    时间戳是 ISO 字符串，转成负的序号即可；解析失败排最后。
    """
    text = str(value or "")
    if not text:
        return float("inf")
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return float("inf")
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return -stamp.timestamp()


# 封面渐变：按名称散列固定取值，同名菜谱永远同一配色
_COVER_PRESETS = (
    "linear-gradient(135deg, #ffb88c 0%, #de6262 100%)",
    "linear-gradient(135deg, #a8edea 0%, #5fb3d4 100%)",
    "linear-gradient(135deg, #f6d365 0%, #fda085 100%)",
    "linear-gradient(135deg, #c2e9fb 0%, #7f9cf5 100%)",
    "linear-gradient(135deg, #d4fc79 0%, #4ca46f 100%)",
    "linear-gradient(135deg, #ffd6a5 0%, #b56576 100%)",
)

# 标签 → 默认图标（用户没传 emoji 时用）
_TAG_EMOJI: dict[str, str] = {
    "soup": "🍲",
    "staple": "🍚",
    "meat": "🍖",
    "veg": "🥬",
    "light": "🥗",
    "spicy": "🌶️",
    "quick": "⏱️",
    "warming": "🍜",
}


def _default_cover(name: str) -> str:
    if not name:
        return _COVER_PRESETS[0]
    return _COVER_PRESETS[sum(ord(ch) for ch in name) % len(_COVER_PRESETS)]


def _default_emoji(tags: list[str]) -> str:
    for tag in tags:
        if tag in _TAG_EMOJI:
            return _TAG_EMOJI[tag]
    return "🍽️"
