"""
tests/test_api.py — 后端自测脚本

覆盖：
    · 存储层：原子写入、损坏自愈、并发写
    · 服务层：点餐增删改、一键生成、营养计算
    · API 层：全部接口的请求/响应与错误码

运行方式（在 server 目录下）：
    python -m tests.test_api
    python tests/test_api.py

不依赖 pytest，全部用标准库 assert，失败会打印具体用例。
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import bootstrap, build_context  # noqa: E402
from app.api.router import create_server  # noqa: E402
from app.services.order_service import OrderError  # noqa: E402
from app.storage.json_store import JsonStore  # noqa: E402

PASSED = 0
FAILED: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED.append(name)
        print(f"  [FAIL] {name} {detail}")


def section(title: str) -> None:
    print(f"\n── {title} " + "─" * max(0, 50 - len(title)))


# ── 存储层 ──────────────────────────────────────────────────────

def test_json_store() -> None:
    section("存储层 · JsonStore")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "demo.json"
        store = JsonStore(path, dict)

        # 首次读取应返回默认值并落盘
        data = store.read()
        check("不存在时返回默认值", data == {})
        check("默认值已落盘", path.exists())

        store.write({"a": 1, "中文": "值"})
        check("写入后可读回", store.read() == {"a": 1, "中文": "值"})
        check("中文不转义", "中文" in path.read_text(encoding="utf-8"))

        # update 事务
        result = store.update(lambda d: {**d, "b": 2})
        check("update 返回新数据", result == {"a": 1, "中文": "值", "b": 2})

        # 损坏自愈
        path.write_text("{ 这不是合法 JSON", encoding="utf-8")
        recovered = store.read()
        check("损坏文件回落默认值", recovered == {})
        backups = list((Path(tmp) / "backups").glob("*.corrupt-*"))
        check("损坏文件已备份", len(backups) == 1, f"实际 {len(backups)} 个")

        # 并发写入不丢数据
        counter_store = JsonStore(Path(tmp) / "counter.json", lambda: {"n": 0})

        def bump() -> None:
            for _ in range(20):
                counter_store.update(lambda d: {"n": d["n"] + 1})

        threads = [threading.Thread(target=bump) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        check("并发写入无丢失", counter_store.read()["n"] == 100,
              f"实际 {counter_store.read()['n']}")


# ── 服务层 ──────────────────────────────────────────────────────

def test_services() -> None:
    section("服务层 · 点餐与营养")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        order = ctx.order

        # 隔离维度：注册一个用户，取其 userId 与 familyId
        account = ctx.auth.register("svc_user", "password1")
        user_id = account["user"]["id"]
        family = account["user"]["familyId"]

        check("菜品库已种子化", len(repo.recipe_ids()) == 39, f"实际 {len(repo.recipe_ids())}")

        week = order.get_week(family)
        check("初始整周为空", week["isEmpty"] is True)
        check("初始 7 天结构完整", len(week["days"]) == 7)

        # 加入
        order.add_item(family, "tomato-beef", "mon", "lunch")
        order.add_item(family, "tomato-beef", "mon", "lunch")
        week = order.get_week(family)
        mon_lunch = week["days"][0]["meals"]["lunch"]
        check("重复加入累加数量", mon_lunch["count"] == 1 and mon_lunch["items"][0]["qty"] == 2,
              f"实际 {mon_lunch}")

        # 修改数量
        order.set_quantity(family, "tomato-beef", "mon", "lunch", 5)
        week = order.get_week(family)
        check("修改数量生效", week["days"][0]["meals"]["lunch"]["items"][0]["qty"] == 5)

        # 数量 0 = 移除
        order.set_quantity(family, "tomato-beef", "mon", "lunch", 0)
        week = order.get_week(family)
        check("数量为 0 时移除条目", week["days"][0]["meals"]["lunch"]["count"] == 0)

        # 非法参数
        try:
            order.add_item(family, "not-exist", "mon", "lunch")
            check("不存在的菜品被拒绝", False)
        except OrderError:
            check("不存在的菜品被拒绝", True)

        try:
            order.add_item(family, "rice", "invalid-day", "lunch")
            check("非法日期被拒绝", False)
        except OrderError:
            check("非法日期被拒绝", True)

        # 一键生成
        generated = order.generate_week(family)
        check("生成后整周非空", generated["isEmpty"] is False)
        check("生成覆盖 7 天", len(generated["days"]) == 7)
        empty_meals = [
            f"{d['label']}·{m}"
            for d in generated["days"]
            for m in ("breakfast", "lunch", "dinner")
            if d["meals"][m]["isEmpty"]
        ]
        check("生成后无空餐次", not empty_meals, f"空餐次: {empty_meals}")

        # 营养：完成度应基于日均，而不是整周合计
        nutrition = order.get_nutrition(family)
        calories = next(p for p in nutrition["progress"] if p["key"] == "calorie")
        check("营养进度按日均比较", calories["percent"] < 200,
              f"实际 {calories['percent']}%")
        check("日均值 = 总量 / 已排天数",
              abs(calories["dailyAvg"] - calories["total"] / nutrition["plannedDays"]) < 0.2)

        # 清空
        cleared = order.clear_week(family)
        check("清空后整周为空", cleared["isEmpty"] is True)

        # 收藏
        fav = ctx.favorite
        fav.add(user_id, "mapo-tofu")
        check("收藏生效", fav.list(user_id)["total"] == 1)
        fav.add(user_id, "mapo-tofu")
        check("重复收藏不重复", fav.list(user_id)["total"] == 1)
        toggled = fav.toggle(user_id, "mapo-tofu")
        check("toggle 取消收藏", toggled["favorite"] is False)
        try:
            fav.add(user_id, "not-exist")
            check("收藏不存在的菜品被拒绝", False)
        except Exception:
            check("收藏不存在的菜品被拒绝", True)


# ── API 层 ──────────────────────────────────────────────────────

def _request(port: int, method: str, path: str, body: dict | None = None, token: str | None = None):
    # URL 里的中文（如搜索关键词）需要百分号编码，否则 urllib 会报 ascii 编码错误
    safe_path = urllib.parse.quote(path, safe="/?=&")
    url = f"http://127.0.0.1:{port}{safe_path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def test_api() -> None:
    section("API 层 · HTTP 接口")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        server = create_server("127.0.0.1", 0, ctx, quiet=True)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status, payload = _request(port, "GET", "/api/health")
            check("GET /api/health", status == 200 and payload["ok"] is True)

            # 注册并取得 token，后续接口都需要登录
            status, payload = _request(
                port, "POST", "/api/auth/register",
                {"username": "api_tester", "password": "password1"},
            )
            check("注册取得 token", status == 200 and bool(payload["data"]["token"]))
            token = payload["data"]["token"]

            status, payload = _request(port, "GET", "/api/dishes", token=token)
            check("GET /api/dishes 返回 39 道", payload["data"]["total"] == 39,
                  f"实际 {payload['data']['total']}")
            check("分类计数齐全", set(payload["data"]["counts"]) >= {"all", "meat", "veg", "soup", "staple"})

            status, payload = _request(port, "GET", "/api/dishes?tag=meat", token=token)
            meat_count = payload["data"]["total"]
            check("按分类筛选生效", 0 < meat_count < 39, f"荤菜 {meat_count}")

            status, payload = _request(port, "GET", "/api/dishes?q=豆腐", token=token)
            check("关键词搜索生效", payload["data"]["total"] >= 1)

            status, payload = _request(port, "GET", "/api/dishes/mapo-tofu", token=token)
            detail = payload["data"]
            check("GET 食谱详情", status == 200 and detail["name"] == "家常麻婆豆腐")
            check("详情含食材与步骤", len(detail["ingredients"]) > 0 and detail["stepCount"] > 0)
            check("详情含标签中文", len(detail["tagMeta"]) > 0)

            status, payload = _request(port, "GET", "/api/dishes/not-exist", token=token)
            check("详情 404", status == 404 and payload["ok"] is False)

            status, payload = _request(port, "GET", "/api/menu", token=token)
            check("GET /api/menu 初始为空", payload["data"]["isEmpty"] is True)

            status, payload = _request(port, "POST", "/api/menu/items",
                                       {"dishId": "mapo-tofu", "day": "wed", "meal": "dinner"}, token=token)
            check("POST 加入菜品", status == 200 and payload["data"]["totals"]["items"] == 1)

            status, payload = _request(port, "POST", "/api/menu/items", {"dishId": "mapo-tofu"}, token=token)
            check("缺参数返回 400", status == 400)

            status, payload = _request(port, "PATCH", "/api/menu/items",
                                       {"dishId": "mapo-tofu", "day": "wed", "meal": "dinner", "qty": 4}, token=token)
            wed = next(d for d in payload["data"]["days"] if d["key"] == "wed")
            check("PATCH 修改数量", wed["meals"]["dinner"]["items"][0]["qty"] == 4)

            status, payload = _request(port, "DELETE",
                                       "/api/menu/items?dishId=mapo-tofu&day=wed&meal=dinner", token=token)
            check("DELETE 移除菜品", payload["data"]["totals"]["items"] == 0)

            status, payload = _request(port, "POST", "/api/menu/generate", token=token)
            check("POST 一键生成", payload["data"]["isEmpty"] is False)
            check("生成 56 项", payload["data"]["totals"]["items"] == 56,
                  f"实际 {payload['data']['totals']['items']}")

            status, payload = _request(port, "GET", "/api/nutrition", token=token)
            check("GET /api/nutrition", status == 200 and len(payload["data"]["progress"]) == 5)

            status, payload = _request(port, "POST", "/api/menu/clear", token=token)
            check("POST 清空", payload["data"]["isEmpty"] is True)

            status, payload = _request(port, "GET", "/api/nope", token=token)
            check("未知接口 404", status == 404)

            status, payload = _request(port, "PUT", "/api/menu", token=token)
            check("不支持的方法 405", status == 405)

            # 静态资源
            status, payload = _request(port, "GET", "/api/meta", token=token)
            check("GET /api/meta", status == 200 and payload["data"]["dishCount"] == 39)
        finally:
            server.shutdown()
            server.server_close()


def main() -> int:
    print("=" * 60)
    print("  今日食堂后端自测")
    print("=" * 60)
    test_json_store()
    test_services()
    test_api()

    print("\n" + "=" * 60)
    print(f"  通过 {PASSED} 项，失败 {len(FAILED)} 项")
    if FAILED:
        for name in FAILED:
            print(f"    - {name}")
        print("=" * 60)
        return 1
    print("  全部通过 ✔")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
