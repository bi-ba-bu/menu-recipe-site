"""
tests/test_family.py — 家庭管理自测

覆盖：
    · 注册自动建家庭（用户即家长）
    · 邀请码加入、重复加入、无效邀请码
    · 一个用户属于多个家庭，可切换且菜单随之变化
    · 收藏不随家庭切换（始终按用户隔离）
    · 家长权限：移除成员、重命名、重置邀请码、解散
    · 成员权限：不能移除他人、不能改家庭名、可主动退出
    · 边界：家长不能退出、不能解散最后一个家庭、被移除后需回落到其他家庭

运行：python -m tests.test_family
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
from app.services.family_service import FamilyError  # noqa: E402

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


# ── 服务层 ──────────────────────────────────────────────────────

def test_family_service() -> None:
    section("服务层 · 家庭管理")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)

        # 注册两人，各自有家庭且是家长
        a = ctx.auth.register("alice", "password1", "小A")["user"]
        b = ctx.auth.register("bob", "password2", "小B")["user"]
        a_id, b_id = a["id"], b["id"]

        check("注册后自动有家庭", a["familyCount"] == 1)
        check("注册者角色是家长", a["role"] == "owner")

        families = ctx.family.list_my_families(a_id, a["familyId"])
        check("家庭列表可查", families["total"] == 1)
        check("当前家庭被标记", families["items"][0]["isActive"] is True)

        a_family = repo.get_family(a["familyId"])
        check("家庭有邀请码", bool(a_family.get("inviteCode")))
        code = a_family["inviteCode"]

        # B 用邀请码加入 A 的家庭
        joined = ctx.family.join_by_code(b_id, code)
        check("凭邀请码加入成功", joined["memberCount"] == 2)
        check("加入后 B 的角色是成员", joined["role"] == "member")

        b_families = ctx.family.list_my_families(b_id, b["familyId"])
        check("B 现在有两个家庭", b_families["total"] == 2)

        # 重复加入
        try:
            ctx.family.join_by_code(b_id, code)
            check("重复加入被拒绝", False)
        except FamilyError as exc:
            check("重复加入被拒绝", "已经在这个家庭" in str(exc))

        # 无效邀请码
        try:
            ctx.family.join_by_code(b_id, "XXXXXX")
            check("无效邀请码被拒绝", False)
        except FamilyError as exc:
            check("无效邀请码被拒绝", "邀请码无效" in str(exc))

        # 同一家庭菜单共享
        ctx.order.add_item(a["familyId"], "rice", "mon", "lunch")
        shared = ctx.order.get_week(a["familyId"])
        check("家庭成员共享菜单", shared["totals"]["items"] == 1)

        # B 的默认家庭菜单仍是空的
        own = ctx.order.get_week(b["familyId"])
        check("B 自己的家庭菜单独立", own["totals"]["items"] == 0)

        # 收藏不随家庭变化
        ctx.favorite.add(b_id, "mapo-tofu")
        check("收藏按用户存", ctx.favorite.list(b_id)["total"] == 1)
        check("A 看不到 B 的收藏", ctx.favorite.list(a_id)["total"] == 0)

        # ── 权限校验 ──
        try:
            ctx.family.remove_member(a["familyId"], b_id, a_id)
            check("成员不能移除他人", False)
        except FamilyError as exc:
            check("成员不能移除他人", "只有家长" in str(exc))

        try:
            ctx.family.rename_family(a["familyId"], b_id, "改名")
            check("成员不能改名", False)
        except FamilyError:
            check("成员不能改名", True)

        try:
            ctx.family.reset_invite_code(a["familyId"], b_id)
            check("成员不能重置邀请码", False)
        except FamilyError:
            check("成员不能重置邀请码", True)

        # ── 家长能力 ──
        renamed = ctx.family.rename_family(a["familyId"], a_id, "小A的家")
        check("家长可改名", renamed["name"] == "小A的家")

        old_code = repo.get_family(a["familyId"])["inviteCode"]
        reset = ctx.family.reset_invite_code(a["familyId"], a_id)
        check("家长可重置邀请码", reset["inviteCode"] != old_code)

        # 成员可主动退出
        ctx.family.leave_family(a["familyId"], b_id)
        check("成员可主动退出", not ctx.family.is_member(repo.get_family(a["familyId"]), b_id))

        # 家长不能退出自己的家庭
        try:
            ctx.family.leave_family(a["familyId"], a_id)
            check("家长不能退出", False)
        except FamilyError as exc:
            check("家长不能退出", "家长不能退出" in str(exc))

        # 家长不能移除自己
        try:
            ctx.family.remove_member(a["familyId"], a_id, a_id)
            check("家长不能移除自己", False)
        except FamilyError:
            check("家长不能移除自己", True)

        # 不能解散最后一个自建家庭
        try:
            ctx.family.dissolve_family(a["familyId"], a_id)
            check("不能解散最后一个家庭", False)
        except FamilyError as exc:
            check("不能解散最后一个家庭", "至少需要保留" in str(exc))

        # 建第二个家庭后可以解散第一个
        second = ctx.family.create_family(a_id, "第二个家")
        check("可以创建多个家庭", ctx.family.list_my_families(a_id, "")["total"] == 2)
        ctx.family.dissolve_family(a["familyId"], a_id)
        check("解散后家庭减少", ctx.family.list_my_families(a_id, "")["total"] == 1)
        check("解散同时清理菜单", ctx.repo.get_week_orders(a["familyId"])["mon"]["lunch"] == [])


# ── 多家庭切换 ──────────────────────────────────────────────────

def test_switch() -> None:
    section("服务层 · 家庭切换")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)

        a = ctx.auth.register("owner1", "password1", "家长")["user"]
        b = ctx.auth.register("member1", "password2", "成员")["user"]

        # B 加入 A 的家
        code = repo.get_family(a["familyId"])["inviteCode"]
        ctx.family.join_by_code(b["id"], code)

        # 两个家庭各放不同的菜
        ctx.order.add_item(a["familyId"], "rice", "mon", "lunch")
        ctx.order.add_item(b["familyId"], "mapo-tofu", "tue", "dinner")

        # B 登录 → 默认是自己的家（列表里自己当家长的排第一）
        login = ctx.auth.login("member1", "password2")
        check("登录后默认进自己的家庭", login["user"]["familyId"] == b["familyId"])
        check("自己的家菜单 1 项", ctx.order.get_week(login["user"]["familyId"])["totals"]["items"] == 1)

        # B 切到 A 的家
        switched = ctx.auth.switch_family(login["token"], b, a["familyId"])
        check("切换成功", switched["familyId"] == a["familyId"])
        check("切换后角色变为成员", switched["role"] == "member")
        check("切换后菜单是 A 家的", ctx.order.get_week(switched["familyId"])["totals"]["items"] == 1)

        # 会话里记录了当前家庭
        session = ctx.auth.get_session(login["token"])
        check("会话记录当前家庭", session.get("currentFamilyId") == a["familyId"])

        # 重新登录记住上次选择
        relogin = ctx.auth.login("member1", "password2")
        check("重新登录记住上次家庭", relogin["user"]["familyId"] == a["familyId"])

        # 不能切到没加入的家庭
        c = ctx.auth.register("outsider", "password3", "外人")["user"]
        try:
            ctx.auth.switch_family(login["token"], b, c["familyId"])
            check("不能切到未加入的家庭", False)
        except FamilyError as exc:
            check("不能切到未加入的家庭", "不在这个家庭" in str(exc))

        # 被家长移除后，自动回落到自己的家庭
        ctx.family.remove_member(a["familyId"], a["id"], b["id"])
        resolved = ctx.family.resolve_active_family(b, a["familyId"])
        check("被移除后回落到自己的家", resolved["id"] == b["familyId"])


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


def test_api_family() -> None:
    section("API 层 · 家庭接口")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        server = create_server("127.0.0.1", 0, ctx, quiet=True)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            # 家长注册
            _, p = _request(port, "POST", "/api/auth/register",
                            {"username": "papa", "password": "password1", "displayName": "爸爸"})
            token_a = p["data"]["token"]
            family_a = p["data"]["user"]["familyId"]

            # 成员注册
            _, p = _request(port, "POST", "/api/auth/register",
                            {"username": "kid", "password": "password2", "displayName": "孩子"})
            token_b = p["data"]["token"]

            # 获取邀请码（只有家长能看到）
            _, detail = _request(port, "GET", f"/api/families/{family_a}", token=token_a)
            code = detail["data"]["inviteCode"]
            check("家长可见邀请码", bool(code))

            # 成员用邀请码加入
            status, joined = _request(port, "POST", "/api/families/join", {"code": code}, token=token_b)
            check("加入家庭 200", status == 200 and joined["data"]["memberCount"] == 2)

            # 成员看不到邀请码
            _, detail_b = _request(port, "GET", f"/api/families/{family_a}", token=token_b)
            check("成员看不到邀请码", detail_b["data"]["inviteCode"] == "")

            # 家庭成员列表包含两人
            names = [m["displayName"] for m in detail_b["data"]["members"]]
            check("成员列表完整", "爸爸" in names and "孩子" in names)

            # 家庭列表接口
            _, mine = _request(port, "GET", "/api/families", token=token_b)
            check("B 有 2 个家庭", mine["data"]["total"] == 2)

            # 切换家庭
            status, sw = _request(port, "POST", f"/api/families/{family_a}/switch", token=token_b)
            check("切换家庭 200", status == 200 and sw["data"]["familyId"] == family_a)
            _, me = _request(port, "GET", "/api/auth/me", token=token_b)
            check("me 反映当前家庭", me["data"]["familyId"] == family_a)

            # 切换后菜单与家长一致
            _request(port, "POST", "/api/menu/items",
                     {"dishId": "rice", "day": "mon", "meal": "lunch"}, token=token_a)
            _, menu_b = _request(port, "GET", "/api/menu", token=token_b)
            check("切换后看到家长家的菜单", menu_b["data"]["totals"]["items"] == 1)

            # 成员尝试移除家长 → 400
            _, me_a = _request(port, "GET", "/api/auth/me", token=token_a)
            a_id = me_a["data"]["id"]
            status, err = _request(
                port, "DELETE", f"/api/families/{family_a}/members/{a_id}", token=token_b
            )
            check("成员移除他人被拒绝", status == 400)

            # 家长移除成员
            _, me_b = _request(port, "GET", "/api/auth/me", token=token_b)
            b_id = me_b["data"]["id"]
            status, removed = _request(
                port, "DELETE", f"/api/families/{family_a}/members/{b_id}", token=token_a
            )
            check("家长移除成员成功", status == 200 and removed["data"]["memberCount"] == 1)

            # 被移除后自动回落到自己的家庭
            _, me_b2 = _request(port, "GET", "/api/auth/me", token=token_b)
            check("被移除后回到自己的家", me_b2["data"]["familyId"] != family_a)

            # 创建新家庭
            status, created = _request(port, "POST", "/api/families", {"name": "新家"}, token=token_b)
            check("创建家庭 200", status == 200 and created["data"]["name"] == "新家")

            # 重命名（家长）
            status, renamed = _request(port, "PATCH", f"/api/families/{family_a}",
                                       {"name": "爸爸的家"}, token=token_a)
            check("重命名成功", status == 200 and renamed["data"]["name"] == "爸爸的家")

            # 成员不能重命名（B 已不在 A 家，应 403）
            status, _ = _request(port, "PATCH", f"/api/families/{family_a}",
                                 {"name": "乱改"}, token=token_b)
            check("非成员改家庭名被拒绝", status == 403)

            # 退出家庭
            code2 = created["data"]["inviteCode"]
            _request(port, "POST", "/api/families/join", {"code": code2}, token=token_a)
            status, left = _request(port, "POST", f"/api/families/{created['data']['id']}/leave",
                                    token=token_a)
            check("成员退出家庭成功", status == 200)

            # 解散家庭（B 有两个家，可解散新家）
            status, dis = _request(port, "DELETE", f"/api/families/{created['data']['id']}",
                                   token=token_b)
            check("解散家庭成功", status == 200)
        finally:
            server.shutdown()
            server.server_close()


def main() -> int:
    print("=" * 60)
    print("  家庭管理自测")
    print("=" * 60)
    test_family_service()
    test_switch()
    test_api_family()

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
