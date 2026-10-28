"""
services/order_service.py — 点餐与一周菜单服务

对应前端展示：
    · 一周菜单页：按天 / 餐次展示已排菜品、每日热量汇总、星期切换角标
    · 点餐页：加入菜品、数量步进、移除单条、清空
    · 一键生成：按营养搭配规则自动排满一周
    · 营养概览：按订单实时计算每日摄入（不单独落盘，避免两份数据不一致）
"""

from __future__ import annotations

import random
from typing import Any

from ..seed import GENERATE_POOL
from ..storage.repository import (
    DAY_KEYS,
    MEALS,
    MEAL_KEYS,
    Repository,
    empty_week,
)


class OrderError(Exception):
    """点餐业务异常（参数非法等）。"""


# 日期元数据（含示例日期，便于前端展示"10/20"这类角标）
DAYS_META: tuple[dict[str, str], ...] = (
    {"key": "mon", "label": "周一", "date": "10/20"},
    {"key": "tue", "label": "周二", "date": "10/21"},
    {"key": "wed", "label": "周三", "date": "10/22"},
    {"key": "thu", "label": "周四", "date": "10/23"},
    {"key": "fri", "label": "周五", "date": "10/24"},
    {"key": "sat", "label": "周六", "date": "10/25"},
    {"key": "sun", "label": "周日", "date": "10/26"},
)


def _dish_view(dish_id: str, qty: int, recipes: dict[str, Any]) -> dict[str, Any] | None:
    """把订单条目展开成前端可直接渲染的菜品视图。"""
    recipe = recipes.get(dish_id)
    if recipe is None:
        return None
    nutrition = recipe.get("nutrition") or {}
    tags = recipe.get("tags") or []
    name = recipe.get("name", "")
    return {
        "id": dish_id,
        "name": f"{name} ×{qty}" if qty > 1 else name,
        "baseName": name,
        "qty": qty,
        "time": recipe.get("time", 0),
        "tags": tags,
        "spicy": "spicy" in tags,
        # 数量已折算进热量，前端直接相加即可
        "calorie": nutrition.get("calorie", 0) * qty,
        "protein": nutrition.get("protein", 0) * qty,
        "fat": nutrition.get("fat", 0) * qty,
        "carb": nutrition.get("carb", 0) * qty,
        "fiber": nutrition.get("fiber", 0) * qty,
    }


class OrderService:
    """点餐订单的读写与统计。"""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    # ── 校验 ────────────────────────────────────────────────────

    def _validate_slot(self, day: str, meal: str) -> None:
        if day not in DAY_KEYS:
            raise OrderError(f"无效的日期：{day}")
        if meal not in MEAL_KEYS:
            raise OrderError(f"无效的餐次：{meal}")

    def _require_dish(self, dish_id: str) -> dict[str, Any]:
        recipe = self.repo.get_recipe(dish_id)
        if recipe is None:
            raise OrderError(f"菜品不存在：{dish_id}")
        return recipe

    # ── 查询 ────────────────────────────────────────────────────

    def get_week(self, family_id: str, week_key: str | None = None) -> dict[str, Any]:
        """
        返回一周菜单的完整视图：
            days        每天的三餐明细 + 当日合计
            totals      整周合计
            isEmpty     整周是否为空（前端显示空态 / 一键生成入口）
        """
        week = self.repo.get_week_orders(family_id, week_key)
        recipes = self.repo.all_recipes()
        config = self.repo.get_config()

        days_out: list[dict[str, Any]] = []
        week_totals = {"items": 0, "calorie": 0, "protein": 0, "fat": 0, "carb": 0, "fiber": 0}

        for day_meta in DAYS_META:
            day_key = day_meta["key"]
            bucket = week.get(day_key) or {}

            meals_out: dict[str, Any] = {}
            day_items = 0
            day_calorie = 0

            for meal_meta in MEALS:
                meal_key = meal_meta["key"]
                entries = bucket.get(meal_key) or []
                views = []
                for entry in entries:
                    view = _dish_view(entry["id"], entry["qty"], recipes)
                    if view is None:
                        continue
                    views.append(view)
                    day_items += 1
                    day_calorie += view["calorie"]
                meals_out[meal_key] = {
                    "label": meal_meta["label"],
                    "items": views,
                    "count": len(views),
                    # 某一餐未安排时前端显示"未安排"
                    "isEmpty": len(views) == 0,
                }

            # 当日营养合计：从各餐菜品累加
            day_nutrition = {"calorie": 0, "protein": 0, "fat": 0, "carb": 0, "fiber": 0}
            for meal_data in meals_out.values():
                for item in meal_data["items"]:
                    for key in day_nutrition:
                        day_nutrition[key] += item[key]

            days_out.append(
                {
                    "key": day_key,
                    "label": day_meta["label"],
                    "date": day_meta.get("date", ""),
                    "meals": meals_out,
                    "count": day_items,
                    "calorie": day_calorie,
                    "nutrition": {k: round(v, 1) for k, v in day_nutrition.items()},
                    "isEmpty": day_items == 0,
                }
            )

            for key in week_totals:
                if key == "items":
                    week_totals["items"] += day_items
                else:
                    week_totals[key] += day_nutrition[key]

        week_totals = {k: round(v, 1) if k != "items" else v for k, v in week_totals.items()}

        return {
            "weekKey": week_key or self.repo.active_week_key(family_id),
            "week": config["week"],
            "days": days_out,
            "totals": week_totals,
            "isEmpty": week_totals["items"] == 0,
        }

    def get_nutrition(self, family_id: str, week_key: str | None = None) -> dict[str, Any]:
        """
        营养概览页数据。

        说明：目标的量纲是"每日建议摄入量"，所以完成度按**日均值**比较，
        不能拿整周合计去比单日目标（否则会算出几百个百分点）。
        另外单独给出"已排天数"，未排菜的日子不计入日均，避免被稀释。
        """
        week_view = self.get_week(family_id, week_key)
        config = self.repo.get_config()
        target = config["nutritionTarget"]

        days = [
            {
                "key": d["key"],
                "label": d["label"],
                "calorie": round(d["nutrition"]["calorie"], 1),
                "protein": round(d["nutrition"]["protein"], 1),
                "fat": round(d["nutrition"]["fat"], 1),
                "carb": round(d["nutrition"]["carb"], 1),
                "fiber": round(d["nutrition"]["fiber"], 1),
                "isEmpty": d["isEmpty"],
            }
            for d in week_view["days"]
        ]

        # 只统计已安排菜品的日子
        planned = [d for d in week_view["days"] if not d["isEmpty"]]
        planned_count = len(planned) or 1
        totals = week_view["totals"]

        progress = []
        for key, label, unit in (
            ("calorie", "热量", "千卡"),
            ("protein", "蛋白质", "克"),
            ("fat", "脂肪", "克"),
            ("carb", "碳水化合物", "克"),
            ("fiber", "膳食纤维", "克"),
        ):
            goal = target.get(key, 1) or 1
            total_value = totals.get(key, 0)
            daily_avg = round(total_value / planned_count, 1)
            progress.append(
                {
                    "key": key,
                    "label": label,
                    "unit": unit,
                    "total": total_value,
                    "dailyAvg": daily_avg,
                    "target": goal,
                    "percent": round(daily_avg / goal * 100),
                }
            )

        water = config.get("water", {"current": 0, "target": 2000})
        return {
            "days": days,
            "progress": progress,
            "water": water,
            "target": target,
            "plannedDays": len(planned),
            "totals": totals,
        }

    # ── 写入 ────────────────────────────────────────────────────

    def add_item(
        self,
        family_id: str,
        dish_id: str,
        day: str,
        meal: str,
        qty: int = 1,
        week_key: str | None = None,
    ) -> dict[str, Any]:
        """
        加入一道菜。

        同一道菜在同一天同一餐重复加入时数量累加，不产生重复条目。
        """
        self._validate_slot(day, meal)
        self._require_dish(dish_id)

        try:
            add_qty = max(1, min(99, int(qty)))
        except (TypeError, ValueError):
            add_qty = 1

        week = self.repo.get_week_orders(family_id, week_key)
        entries = week[day][meal]
        existing = next((e for e in entries if e["id"] == dish_id), None)
        if existing:
            existing["qty"] = min(99, existing["qty"] + add_qty)
        else:
            entries.append({"id": dish_id, "qty": add_qty})

        self.repo.save_week_orders(family_id, week, week_key)
        return self.get_week(family_id, week_key)

    def set_quantity(
        self,
        family_id: str,
        dish_id: str,
        day: str,
        meal: str,
        qty: int,
        week_key: str | None = None,
    ) -> dict[str, Any]:
        """设置数量；数量为 0 时等价于移除。"""
        self._validate_slot(day, meal)

        try:
            new_qty = int(qty)
        except (TypeError, ValueError):
            raise OrderError("数量必须是整数")

        week = self.repo.get_week_orders(family_id, week_key)
        entries = week[day][meal]
        idx = next((i for i, e in enumerate(entries) if e["id"] == dish_id), -1)
        if idx < 0:
            raise OrderError("该菜品不在此餐次中")

        if new_qty <= 0:
            entries.pop(idx)
        else:
            entries[idx]["qty"] = min(99, new_qty)

        self.repo.save_week_orders(family_id, week, week_key)
        return self.get_week(family_id, week_key)

    def remove_item(
        self,
        family_id: str,
        dish_id: str,
        day: str,
        meal: str,
        week_key: str | None = None,
    ) -> dict[str, Any]:
        """从菜单中移除某道菜。"""
        self._validate_slot(day, meal)

        week = self.repo.get_week_orders(family_id, week_key)
        before = len(week[day][meal])
        week[day][meal] = [e for e in week[day][meal] if e["id"] != dish_id]
        if len(week[day][meal]) == before:
            raise OrderError("该菜品不在此餐次中")

        self.repo.save_week_orders(family_id, week, week_key)
        return self.get_week(family_id, week_key)

    def clear_week(self, family_id: str, week_key: str | None = None) -> dict[str, Any]:
        """清空整周安排。"""
        self.repo.save_week_orders(family_id, empty_week(), week_key)
        return self.get_week(family_id, week_key)

    # ── 一键生成 ────────────────────────────────────────────────

    def generate_week(self, family_id: str, week_key: str | None = None) -> dict[str, Any]:
        """
        一键生成整周菜单。

        搭配规则：
            早餐：1 主食 + 1 其他
            午餐：1 主食 + 1 荤 + 1 素
            晚餐：1 主食 + 1 荤或素 + 1 汤
        去重策略：优先选本周没用过的菜，池子取尽后允许复用。
        """
        week = empty_week()
        used: set[str] = set()

        for day in DAY_KEYS:
            for meal in MEAL_KEYS:
                pool = GENERATE_POOL.get(meal, [])
                picked = self._build_meal(meal, pool, used)
                week[day][meal] = [{"id": dish_id, "qty": 1} for dish_id in picked]

        self.repo.save_week_orders(family_id, week, week_key)
        return self.get_week(family_id, week_key)

    def _build_meal(self, meal: str, pool: list[str], used: set[str]) -> list[str]:
        """按餐次规则从候选池挑菜。"""
        recipes = self.repo.all_recipes()
        result: list[str] = []

        def has_tag(dish_id: str, tag: str) -> bool:
            return tag in (recipes.get(dish_id, {}).get("tags") or [])

        def take(predicate) -> str | None:
            candidates = [
                d for d in pool if predicate(d) and d not in result and d not in used
            ]
            if not candidates:  # 没用过的取完了，允许复用
                candidates = [d for d in pool if predicate(d) and d not in result]
            if not candidates:
                return None
            chosen = random.choice(candidates)
            used.add(chosen)
            result.append(chosen)
            return chosen

        take(lambda d: has_tag(d, "staple"))

        if meal == "breakfast":
            take(lambda d: not has_tag(d, "staple"))
        elif meal == "lunch":
            take(lambda d: has_tag(d, "meat"))
            take(lambda d: has_tag(d, "veg"))
        else:
            take(lambda d: has_tag(d, "meat") or has_tag(d, "veg"))
            take(lambda d: has_tag(d, "soup"))

        if not result:  # 兜底
            take(lambda d: True)
        return result
