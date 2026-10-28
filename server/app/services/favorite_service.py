"""
services/favorite_service.py — 收藏服务

对应前端展示：我的收藏页（收藏卡片列表 + 侧栏徽标计数）
"""

from __future__ import annotations

from typing import Any

from ..storage.repository import Repository


class FavoriteError(Exception):
    """收藏业务异常。"""


class FavoriteService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def list(self, user_id: str) -> dict[str, Any]:
        """收藏列表，附带展示所需字段。"""
        recipes = self.repo.all_recipes()
        items = []
        for dish_id in self.repo.get_favorites(user_id):
            recipe = recipes.get(dish_id)
            if recipe is None:
                continue
            nutrition = recipe.get("nutrition") or {}
            items.append(
                {
                    "id": dish_id,
                    "name": recipe.get("name", ""),
                    "time": recipe.get("time", 0),
                    "difficulty": recipe.get("difficulty", ""),
                    "calorie": nutrition.get("calorie", 0),
                    "tags": recipe.get("tags") or [],
                }
            )
        return {"items": items, "total": len(items)}

    def add(self, user_id: str, dish_id: str) -> dict[str, Any]:
        if dish_id not in self.repo.all_recipes():
            raise FavoriteError(f"菜品不存在：{dish_id}")
        ids = self.repo.get_favorites(user_id)
        if dish_id not in ids:
            ids.append(dish_id)
            self.repo.set_favorites(user_id, ids)
        return self.list(user_id)

    def remove(self, user_id: str, dish_id: str) -> dict[str, Any]:
        ids = [i for i in self.repo.get_favorites(user_id) if i != dish_id]
        self.repo.set_favorites(user_id, ids)
        return self.list(user_id)

    def toggle(self, user_id: str, dish_id: str) -> dict[str, Any]:
        """切换收藏状态，返回最新列表与当前状态。"""
        if dish_id not in self.repo.all_recipes():
            raise FavoriteError(f"菜品不存在：{dish_id}")
        ids = self.repo.get_favorites(user_id)
        if dish_id in ids:
            ids = [i for i in ids if i != dish_id]
            now_favorite = False
        else:
            ids.append(dish_id)
            now_favorite = True
        self.repo.set_favorites(user_id, ids)
        data = self.list(user_id)
        data["favorite"] = now_favorite
        data["dishId"] = dish_id
        return data
