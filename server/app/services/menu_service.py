"""
services/menu_service.py — 菜品与食谱服务

对应前端展示：
    · 点餐橱窗（按分类筛选、关键词搜索）
    · 食谱详情页（营养、食材、步骤、小贴士）

可见性（v2 菜谱体系）：
    · 点餐橱窗只展示"用户可见"的菜谱 = 公共菜谱 + 自己的菜谱
    · 已下架（archived）的菜谱不进入橱窗，但历史菜单仍能正常展示
      （历史菜单走 order_service，按 id 直接读菜谱，不受这里影响）
"""

from __future__ import annotations

from typing import Any

from ..storage.repository import TAG_META
from ..storage.repository import Repository
from .recipe_service import RecipeService


class MenuService:
    """菜品查询、筛选与食谱详情。"""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        # 复用菜谱服务的可见性判定，避免两处规则各写一套而逐渐跑偏
        self.recipes = RecipeService(repo)

    # ── 列表 ────────────────────────────────────────────────────

    def list_dishes(
        self,
        tag: str | None = None,
        q: str | None = None,
        user_id: str = "",
    ) -> dict[str, Any]:
        """
        返回菜品橱窗数据。

        tag: 分类标签（light/meat/veg/soup/staple/spicy/quick/warming）
        q:   关键词，匹配菜名、副标题与食材名
        user_id: 当前用户，用于过滤出"公共 + 自己的"菜谱
        """
        keyword = (q or "").strip().lower()

        # 先按可见性筛出不重复的一批菜谱（含自己的私人菜谱，方便自己点餐）
        recipe_items = self.recipes.visible_recipes(user_id)

        items: list[dict[str, Any]] = []
        for dish_id, recipe in recipe_items:
            tags = recipe.get("tags") or []
            if tag and tag != "all" and tag not in tags:
                continue
            if keyword:
                haystack = " ".join(
                    [
                        recipe.get("name", ""),
                        recipe.get("subtitle", ""),
                        " ".join(ing.get("name", "") for ing in recipe.get("ingredients", [])),
                    ]
                ).lower()
                if keyword not in haystack:
                    continue
            items.append(self._to_summary(dish_id, recipe))

        # 分类计数（基于可见菜品，保证筛选胶囊上的数字与列表条数一致）
        counts = {"all": len(recipe_items)}
        for meta_key in TAG_META:
            counts[meta_key] = sum(
                1 for _, r in recipe_items if meta_key in (r.get("tags") or [])
            )

        return {"items": items, "total": len(items), "counts": counts}

    def _to_summary(self, dish_id: str, recipe: dict[str, Any]) -> dict[str, Any]:
        """列表项：只带橱窗需要的字段，避免传输整份食谱。"""
        nutrition = recipe.get("nutrition") or {}
        return {
            "id": dish_id,
            "name": recipe.get("name", ""),
            "subtitle": recipe.get("subtitle", ""),
            "time": recipe.get("time", 0),
            "difficulty": recipe.get("difficulty", ""),
            "serving": recipe.get("serving", ""),
            "tags": recipe.get("tags") or [],
            "calorie": nutrition.get("calorie", 0),
        }

    # ── 详情 ────────────────────────────────────────────────────

    def get_dish_detail(self, dish_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        """
        食谱详情页所需的完整数据。

        可见性：不存在的菜谱、以及别人的私人/待审核/已下架菜谱都返回 None，
        由 router 统一转成 404，避免通过 id 探测他人未公开的菜谱。
        例外：历史菜单里引用的菜谱必须能正常打开详情，
        所以"已被某个家庭菜单引用"的菜谱不做可见性拦截。
        """
        recipe = self.repo.get_recipe(dish_id)
        if recipe is None:
            return None

        if not self.recipes.is_visible(recipe, user_id or ""):
            # 历史菜单引用过的菜谱仍可查看（下架后历史菜单也要能看）
            if not self.repo.is_recipe_used_by_any_family(dish_id):
                return None

        data = dict(recipe)
        data["id"] = dish_id
        data["isFavorite"] = bool(user_id) and dish_id in self.repo.get_favorites(user_id)

        # 补上标签的中文名与配色，前端无需再维护一份映射
        data["tagMeta"] = [
            {"key": t, **TAG_META[t]} for t in (recipe.get("tags") or []) if t in TAG_META
        ]

        # 步骤总耗时（详情页"共 N 分钟"）
        steps = recipe.get("steps") or []
        data["stepsTotalMinutes"] = sum(int(s.get("minutes") or 0) for s in steps)
        data["stepCount"] = len(steps)
        return data

    # ── 元数据 ──────────────────────────────────────────────────

    def get_meta(self) -> dict[str, Any]:
        """标签字典、周信息等静态元数据，供前端初始化。"""
        config = self.repo.get_config()
        return {
            "tags": TAG_META,
            "week": config["week"],
            "nutritionTarget": config["nutritionTarget"],
            "dishCount": len(self.repo.all_recipes()),
        }
