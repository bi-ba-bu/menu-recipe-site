"""
tests/test_auth.py — 用户体系与隔离性自测

覆盖：
    · 注册 / 登录 / 登出 / 会话失效
    · 密码安全：不落明文、盐随机、错误密码拒绝
    · 用户隔离：收藏互不影响
    · 家庭隔离：同家庭成员菜单一致，不同家庭互不可见（为后续家庭机制预热）
    · 未登录访问受保护接口返回 401

运行：python -m tests.test_auth
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
from app.services.auth_service import AuthError  # noqa: E402

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
    print(f"\n── {title} " + "─" * max(0, 46 - len(title)))


# ── 服务层：注册与密码安全 ──────────────────────────────────────

def test_register_login() -> None:
    section("服务层 · 注册与登录")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        auth = ctx.auth

        result = auth.register("alice", "secret123", "小红")
        check("注册成功返回 token", bool(result["token"]))
        check("返回用户信息", result["user"]["username"] == "alice")
        check("展示名生效", result["user"]["displayName"] == "小红")
        check("自动创建家庭", bool(result["user"]["familyId"]))
        check("家庭名为 xx 的家庭", "小红" in result["user"]["familyName"])
        check("角色为 owner", result["user"]["role"] == "owner")

        # 密码绝不外泄
        check("返回体不含 passwordHash", "passwordHash" not in json.dumps(result))
        check("返回体不含 salt", '"salt"' not in json.dumps(result))

        # 存储层检查
        stored = repo.all_users()[result["user"]["id"]]
        check("存储有 passwordHash", bool(stored.get("passwordHash")))
        check("存储有随机盐", len(stored.get("salt", "")) == 32)
        check("密码不是明文", stored["passwordHash"] != "secret123")
        check("迭代次数已记录", stored.get("iterations", 0) >= 100_000)

        # 同名注册
        try:
            auth.register("alice", "another123")
            check("重复用户名被拒绝", False)
        except AuthError as exc:
            check("重复用户名被拒绝", "已被注册" in str(exc))

        # 大小写不敏感
        try:
            auth.register("ALICE", "another123")
            check("用户名大小写不敏感", False)
        except AuthError:
            check("用户名大小写不敏感", True)

        # 弱密码 / 非法用户名
        for bad_user, bad_pwd, case in [
            ("a", "secret123", "用户名过短"),
            ("bob", "123", "密码过短"),
            ("bad name", "secret123", "含空格"),
            ("bob!", "secret123", "含特殊符号"),
        ]:
            try:
                auth.register(bad_user, bad_pwd)
                check(f"{case}被拒绝", False)
            except AuthError:
                check(f"{case}被拒绝", True)

        # 登录
        login = auth.login("alice", "secret123")
        check("正确密码可登录", bool(login["token"]))
        check("登录 token 与注册不同", login["token"] != result["token"])

        try:
            auth.login("alice", "wrong-password")
            check("错误密码被拒绝", False)
        except AuthError as exc:
            check("错误密码被拒绝", "用户名或密码错误" in str(exc))

        try:
            auth.login("nobody", "whatever")
            check("不存在的用户提示一致", False)
        except AuthError as exc:
            check("不存在的用户提示一致（防枚举）", "用户名或密码错误" in str(exc))

        # 会话解析
        user = auth.resolve_token(login["token"])
        check("token 可解析到用户", user is not None and user["username"] == "alice")
        check("无效 token 返回 None", auth.resolve_token("fake-token") is None)

        # 登出
        auth.logout(login["token"])
        check("登出后 token 失效", auth.resolve_token(login["token"]) is None)

    # 盐随机性：两个相同密码的账号哈希不同
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        ctx.auth.register("u1", "samepassword")
        ctx.auth.register("u2", "samepassword")
        users = list(repo.all_users().values())
        check("相同密码不同哈希（盐随机）", users[0]["passwordHash"] != users[1]["passwordHash"])
        check("相同密码不同盐", users[0]["salt"] != users[1]["salt"])


# ── 服务层：隔离性 ──────────────────────────────────────────────

def test_isolation() -> None:
    section("服务层 · 用户与家庭隔离")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)

        a = ctx.auth.register("user_a", "password1")
        b = ctx.auth.register("user_b", "password2")
        a_id, a_family = a["user"]["id"], a["user"]["familyId"]
        b_id, b_family = b["user"]["id"], b["user"]["familyId"]

        check("两个用户家庭不同", a_family != b_family)

        # 收藏按用户隔离
        ctx.favorite.add(a_id, "mapo-tofu")
        check("A 的收藏生效", ctx.favorite.list(a_id)["total"] == 1)
        check("B 看不到 A 的收藏", ctx.favorite.list(b_id)["total"] == 0)

        ctx.favorite.add(b_id, "tomato-beef")
        check("B 的收藏独立", ctx.favorite.list(b_id)["total"] == 1)
        check("A 的收藏不受影响", ctx.favorite.list(a_id)["total"] == 1)

        # 菜单按家庭隔离
        ctx.order.add_item(a_family, "rice", "mon", "lunch")
        a_menu = ctx.order.get_week(a_family)
        b_menu = ctx.order.get_week(b_family)
        check("A 家庭菜单有菜", a_menu["totals"]["items"] == 1)
        check("B 家庭菜单为空", b_menu["totals"]["items"] == 0)

        ctx.order.generate_week(b_family)
        check("B 生成后 A 仍只有 1 项", ctx.order.get_week(a_family)["totals"]["items"] == 1)
        check("B 生成后有 56 项", ctx.order.get_week(b_family)["totals"]["items"] == 56)

        # 家庭共享：同一家庭的两个成员看到同一份菜单
        ctx.repo.add_family_member(a_family, b_id)
        shared = ctx.order.get_week(a_family)
        check("同家庭成员菜单一致", shared["totals"]["items"] == 1)


# ── API 层 ──────────────────────────────────────────────────────

def _request(port: int, method: str, path: str, body: dict | None = None, token: str | None = None):
    safe_path = urllib.parse.quote(path, safe="/?=&")
    url = f"http://127.0.0.1:{port}{safe_path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def test_api_auth() -> None:
    section("API 层 · 鉴权与隔离")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        server = create_server("127.0.0.1", 0, ctx, quiet=True)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            # 未登录访问受保护接口
            for method, path in [
                ("GET", "/api/menu"),
                ("GET", "/api/favorites"),
                ("GET", "/api/nutrition"),
                ("GET", "/api/dishes"),
                ("GET", "/api/auth/me"),
            ]:
                status, payload = _request(port, method, path)
                check(f"未登录 {path} 返回 401", status == 401, f"实际 {status}")

            # 健康检查公开
            status, payload = _request(port, "GET", "/api/health")
            check("health 无需登录", status == 200)

            # 注册
            status, payload = _request(
                port, "POST", "/api/auth/register",
                {"username": "api_user", "password": "pass1234", "displayName": "接口用户"},
            )
            check("注册接口 200", status == 200 and payload["ok"] is True)
            token_a = payload["data"]["token"]

            status, payload = _request(port, "GET", "/api/auth/me", token=token_a)
            check("me 返回当前用户", payload["data"]["username"] == "api_user")
            check("me 不含密码字段", "passwordHash" not in json.dumps(payload))

            # 带 token 访问
            status, payload = _request(port, "GET", "/api/menu", token=token_a)
            check("带 token 访问菜单成功", status == 200)

            # 注册第二个用户
            status, payload = _request(
                port, "POST", "/api/auth/register",
                {"username": "api_user2", "password": "pass1234"},
            )
            token_b = payload["data"]["token"]

            # 收藏隔离
            _request(port, "POST", "/api/favorites", {"dishId": "mapo-tofu"}, token=token_a)
            _, fav_a = _request(port, "GET", "/api/favorites", token=token_a)
            _, fav_b = _request(port, "GET", "/api/favorites", token=token_b)
            check("A 收藏 1 项", fav_a["data"]["total"] == 1)
            check("B 收藏为空（隔离）", fav_b["data"]["total"] == 0)

            # 菜单隔离
            _request(port, "POST", "/api/menu/items",
                     {"dishId": "rice", "day": "mon", "meal": "lunch"}, token=token_a)
            _, menu_a = _request(port, "GET", "/api/menu", token=token_a)
            _, menu_b = _request(port, "GET", "/api/menu", token=token_b)
            check("A 菜单有菜", menu_a["data"]["totals"]["items"] == 1)
            check("B 菜单为空（隔离）", menu_b["data"]["totals"]["items"] == 0)

            # 家庭信息
            _, fam = _request(port, "GET", "/api/family", token=token_a)
            check("家庭接口返回成员", len(fam["data"]["members"]) == 1)

            # 登出后失效
            _request(port, "POST", "/api/auth/logout", token=token_a)
            status, _ = _request(port, "GET", "/api/menu", token=token_a)
            check("登出后 token 失效返回 401", status == 401)

            # 错误密码
            status, payload = _request(
                port, "POST", "/api/auth/login",
                {"username": "api_user", "password": "wrong"},
            )
            check("错误密码返回 400", status == 400)
        finally:
            server.shutdown()
            server.server_close()


def main() -> int:
    print("=" * 60)
    print("  用户体系与隔离性自测")
    print("=" * 60)
    test_register_login()
    test_isolation()
    test_api_auth()

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
