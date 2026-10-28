"""
tests/test_recipe.py — 菜谱维护与审核体系自测

覆盖：
    · 个人菜谱隔离：A 的新增只有 A 看得见，B 看不到也改不了
    · 公共菜谱不可改：系统内置菜谱与审核通过的菜谱都拒绝修改
    · 审核流转：提交 → 通过 → 变公共 → 他人可见且不可改
    · 驳回：记录原因、仅创建者可见、可改后重新提交
    · 撤回：pending → private
    · 下架：从点餐橱窗消失，但历史菜单仍能展示
    · 恢复：archived → private
    · 删除：被菜单引用时拒绝，未被引用时物理删除
    · 非所有者越权：修改 / 下架 / 删除 / 提交 全部被拒
    · 管理员权限：仅 reviewers 名单内账号能看待审核与审核，且不能审自己的菜
    · 参数校验：名称、时长、食材、步骤、标签、难度

运行（在 server 目录下）：
    python -m tests.test_recipe
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
from app.services.recipe_service import (  # noqa: E402
    RecipeError,
    RecipeForbidden,
    RecipeNotFound,
)

PASSED = 0
FAILED: list[str] = []

# 一个可复用的合法菜谱载荷
SAMPLE = {
    "name": "测试番茄炒蛋",
    "subtitle": "十分钟快手家常菜",
    "desc": "番茄炒出沙再加蛋，酸甜适口。",
    "time": 10,
    "difficulty": "简单",
    "serving": "2 人份",
    "tags": ["quick", "veg"],
    "nutrition": {"calorie": 210, "protein": 12, "fat": 14, "carb": 8, "fiber": 1.5},
    "ingredients": [
        {"name": "番茄", "amount": "2 个", "main": True},
        {"name": "鸡蛋", "amount": "3 个", "main": True},
        {"name": "盐", "amount": "2 g"},
    ],
    "steps": [
        {"title": "打蛋", "desc": "鸡蛋打散加少许盐。", "minutes": 2},
        {"title": "炒制", "desc": "热锅下油，先炒蛋再下番茄。", "minutes": 8},
    ],
    "tips": "番茄去皮口感更好。",
}


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


def _expect_error(fn, exc_types, name: str, keyword: str = "") -> None:
    """执行 fn 并断言抛出指定异常（可选断言错误文案包含关键词）。"""
    try:
        fn()
    except exc_types as exc:  # type: ignore[misc]
        if keyword:
            check(name, keyword in str(exc), f"实际提示：{exc}")
        else:
            check(name, True)
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"抛出了意外异常 {type(exc).__name__}: {exc}")
    else:
        check(name, False, "没有抛出异常")


# ── 服务层：基础增删改查与隔离 ──────────────────────────────────

def test_create_and_isolation() -> None:
    section("服务层 · 新增与个人隔离")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe

        alice = ctx.auth.register("alice", "password1", "小A")["user"]
        bob = ctx.auth.register("bob", "password2", "小B")["user"]

        created = svc.create(alice, dict(SAMPLE))
        dish_id = created["id"]

        check("id 形如 r_<12位hex>", dish_id.startswith("r_") and len(dish_id) == 14, dish_id)
        check("新建状态为 private", created["status"] == "private")
        check("新建归属本人", created["ownerId"] == alice["id"] and created["isMine"] is True)
        check("状态中文标签为「个人」", created["statusLabel"] == "个人")
        check("详情带食材与步骤", len(created["ingredients"]) == 3 and created["stepCount"] == 2)
        check("步骤总耗时累加", created["stepsTotalMinutes"] == 10)
        check("未填封面时自动生成", bool(created.get("cover")))
        check("未填图标时按标签生成", created.get("emoji") == "⏱️", created.get("emoji"))
        check("新建可编辑可提交", created["canEdit"] and created["canSubmit"])
        check("新建不可撤回", created["canWithdraw"] is False)

        # 隔离：A 能看到自己的私人菜谱，B 看不到
        alice_list = svc.list_visible(alice)
        bob_list = svc.list_visible(bob)
        alice_ids = [i["id"] for i in alice_list["items"]]
        bob_ids = [i["id"] for i in bob_list["items"]]
        check("A 的列表含自己的新菜谱", dish_id in alice_ids)
        check("B 的列表不含 A 的私人菜谱", dish_id not in bob_ids)
        check("内置菜谱两人都可见", "mapo-tofu" in alice_ids and "mapo-tofu" in bob_ids)
        check("A 的 counts 统计自己的菜谱", alice_list["counts"]["mine"] == 1 and alice_list["counts"]["private"] == 1)
        check("B 的 counts 无个人菜谱", bob_list["counts"]["mine"] == 0)

        # 越权阅读：B 直接按 id 读详情应 404（不泄露存在性）
        _expect_error(lambda: svc.get(bob, dish_id), RecipeNotFound, "B 读 A 的私人菜谱被拒（404）")
        # 越权写入：写操作返回 403（明确告知"这是别人的菜谱"）
        _expect_error(
            lambda: svc.update(bob, dish_id, {"name": "篡改"}),
            RecipeForbidden,
            "B 改 A 的菜谱被拒（403）",
            "无权操作",
        )
        _expect_error(
            lambda: svc.archive(bob, dish_id), RecipeForbidden, "B 下架 A 的菜谱被拒"
        )
        _expect_error(
            lambda: svc.delete(bob, dish_id), RecipeForbidden, "B 删 A 的菜谱被拒"
        )
        _expect_error(
            lambda: svc.submit_review(bob, dish_id), RecipeForbidden, "B 提交 A 的菜谱审核被拒"
        )

        # 修改只改提交的字段，其余沿用原值
        updated = svc.update(alice, dish_id, {"name": "改名后的番茄炒蛋"})
        check("修改名称生效", updated["name"] == "改名后的番茄炒蛋")
        check("未提交的食材保持不变", len(updated["ingredients"]) == 3)
        check("未提交的营养保持不变", updated["nutrition"]["calorie"] == 210)
        check("修改后时间戳更新", bool(updated["updatedAt"]))

        # 点餐橱窗可见性：A 能看到自己新增的，B 看不到
        a_dishes = ctx.menu.list_dishes(user_id=alice["id"])
        b_dishes = ctx.menu.list_dishes(user_id=bob["id"])
        check("橱窗：A 能看到自己的菜谱", any(i["id"] == dish_id for i in a_dishes["items"]))
        check("橱窗：B 看不到别人的私人菜谱", not any(i["id"] == dish_id for i in b_dishes["items"]))
        check("橱窗：A 的数量比 B 多 1", a_dishes["total"] == b_dishes["total"] + 1,
              f"A={a_dishes['total']} B={b_dishes['total']}")

        # 不存在的菜谱
        _expect_error(lambda: svc.get(alice, "not-exist"), RecipeNotFound, "读取不存在的菜谱 404")


# ── 服务层：公共菜谱不可改 ──────────────────────────────────────

def test_public_recipe_readonly() -> None:
    section("服务层 · 公共菜谱只读")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe

        alice = ctx.auth.register("alice", "password1", "小A")["user"]

        seed = repo.get_recipe("mapo-tofu")
        check("内置菜谱状态为 public", seed.get("status") == "public")
        check("内置菜谱归属 system", seed.get("ownerId") == "system")

        view = svc.get(alice, "mapo-tofu")
        check("内置菜谱对普通用户只读", view["canEdit"] is False)
        check("内置菜谱不属于任何人", view["isMine"] is False and view["isPublic"] is True)
        check("内置菜谱不可下架/删除", not view["canArchive"] and not view["canDelete"])
        check("内置菜谱显示系统作者", view["ownerName"] == "系统")

        _expect_error(
            lambda: svc.update(alice, "mapo-tofu", {"name": "篡改"}),
            RecipeForbidden,
            "普通用户改内置菜谱被拒（403）",
            "公共菜谱不可修改",
        )
        _expect_error(
            lambda: svc.archive(alice, "mapo-tofu"), RecipeForbidden, "普通用户下架内置菜谱被拒"
        )
        _expect_error(
            lambda: svc.delete(alice, "mapo-tofu"), RecipeForbidden, "普通用户删内置菜谱被拒"
        )


# ── 服务层：审核流转 ────────────────────────────────────────────

def test_review_flow() -> None:
    section("服务层 · 审核流转")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe

        alice = ctx.auth.register("alice", "password1", "小A")["user"]
        bob = ctx.auth.register("bob", "password2", "小B")["user"]
        admin = ctx.auth.register("admin", "password3", "管理员")["user"]

        check("admin 是审核员", svc.is_reviewer(admin) is True)
        check("alice 不是审核员", svc.is_reviewer(alice) is False)

        dish_id = svc.create(alice, dict(SAMPLE))["id"]

        # 提交审核
        submitted = svc.submit_review(alice, dish_id)
        check("提交后状态为 pending", submitted["status"] == "pending")
        check("提交后带提交时间", bool(submitted["submittedAt"]))
        check("提交后不可编辑", submitted["canEdit"] is False)
        check("提交后可撤回", submitted["canWithdraw"] is True)
        check("已提交不能重复提交", submitted["canSubmit"] is False)

        _expect_error(
            lambda: svc.submit_review(alice, dish_id), RecipeError, "重复提交被拒"
        )
        _expect_error(
            lambda: svc.update(alice, dish_id, {"name": "审核中乱改"}),
            RecipeForbidden,
            "审核中的菜谱不可修改",
        )

        # 非审核员看待审核 / 审核
        _expect_error(
            lambda: svc.list_pending(bob), RecipeForbidden, "非审核员查看待审核被拒", "只有审核员"
        )
        _expect_error(
            lambda: svc.review(bob, dish_id, True), RecipeForbidden, "非审核员审核被拒", "只有审核员"
        )

        # 审核员看到待审核
        pending = svc.list_pending(admin)
        check("待审核列表含该菜谱", any(i["id"] == dish_id for i in pending["items"]))
        check("待审核列表 isReviewer 为真", pending["isReviewer"] is True)

        # 通过
        approved = svc.review(admin, dish_id, True)
        check("审核通过后变 public", approved["status"] == "public")
        check("通过后保留原创建者", approved["ownerId"] == alice["id"])
        check("通过后别人也能看到", dish_id in [i["id"] for i in svc.list_visible(bob)["items"]])

        # 注意：review() 返回的是「审核员视角」的视图，权限标记要拿创建者视角重新读
        as_owner = svc.get(alice, dish_id)
        check("通过后创建者不能再改", as_owner["canEdit"] is False)
        check("通过后仍算自己提交的（isMine）", as_owner["isMine"] is True)
        check("通过后不可下架不可删除",
              as_owner["canArchive"] is False and as_owner["canDelete"] is False)

        # 通过后 B 能读详情、橱窗可见，但仍不能改
        bob_view = svc.get(bob, dish_id)
        check("B 可读已通过菜谱", bob_view["id"] == dish_id and bob_view["isPublic"] is True)
        check("橱窗：B 能看到公共化的菜谱",
              any(i["id"] == dish_id for i in ctx.menu.list_dishes(user_id=bob["id"])["items"]))
        _expect_error(
            lambda: svc.update(alice, dish_id, {"name": "通过后再改"}),
            RecipeForbidden,
            "通过后创建者也改不了",
            "公共菜谱不可修改",
        )

        # 已通过的不在待审核里
        check("通过后离开待审核列表",
              not any(i["id"] == dish_id for i in svc.list_pending(admin)["items"]))

        # 审核不在待审核状态的菜谱
        _expect_error(
            lambda: svc.review(admin, dish_id, True), RecipeError, "重复审核被拒", "不在待审核状态"
        )


def test_reject_flow() -> None:
    section("服务层 · 驳回与重新提交")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe

        alice = ctx.auth.register("alice", "password1", "小A")["user"]
        bob = ctx.auth.register("bob", "password2", "小B")["user"]
        admin = ctx.auth.register("admin", "password3", "管理员")["user"]

        dish_id = svc.create(alice, dict(SAMPLE))["id"]
        svc.submit_review(alice, dish_id)

        _expect_error(
            lambda: svc.review(admin, dish_id, False, ""),
            RecipeError,
            "驳回不填原因被拒",
            "必须填写原因",
        )

        rejected = svc.review(admin, dish_id, False, "步骤描述太简略")
        check("驳回后状态为 rejected", rejected["status"] == "rejected")
        check("驳回原因已记录", rejected["reviewNote"] == "步骤描述太简略")
        check("驳回后仍仅创建者可见",
              dish_id not in [i["id"] for i in svc.list_visible(bob)["items"]])
        check("驳回后仍归属创建者", rejected["ownerId"] == alice["id"])

        # 权限标记以创建者视角为准
        as_owner = svc.get(alice, dish_id)
        check("驳回后可改可重提", as_owner["canEdit"] and as_owner["canSubmit"])

        # 修改后自动清空驳回原因
        fixed = svc.update(alice, dish_id, {"steps": SAMPLE["steps"] + [
            {"title": "装盘", "desc": "撒葱花出锅。", "minutes": 1}
        ]})
        check("修改后清空驳回原因", fixed["reviewNote"] == "")
        check("修改后步骤数增加", fixed["stepCount"] == 3)

        # 重新提交 → 通过
        resubmitted = svc.submit_review(alice, dish_id)
        check("驳回后可重新提交", resubmitted["status"] == "pending")
        approved = svc.review(admin, dish_id, True)
        check("重新提交后可通过", approved["status"] == "public")


def test_withdraw() -> None:
    section("服务层 · 撤回审核")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe

        alice = ctx.auth.register("alice", "password1", "小A")["user"]
        admin = ctx.auth.register("admin", "password3", "管理员")["user"]

        dish_id = svc.create(alice, dict(SAMPLE))["id"]
        _expect_error(
            lambda: svc.withdraw_review(alice, dish_id),
            RecipeError,
            "未提交的不能撤回",
            "只有待审核",
        )

        svc.submit_review(alice, dish_id)
        withdrawn = svc.withdraw_review(alice, dish_id)
        check("撤回后回到 private", withdrawn["status"] == "private")
        check("撤回后清空提交时间", withdrawn["submittedAt"] == "")
        check("撤回后恢复可编辑", withdrawn["canEdit"] is True)
        check("撤回后离开待审核列表",
              not any(i["id"] == dish_id for i in svc.list_pending(admin)["items"]))


def test_admin_cannot_review_self() -> None:
    section("服务层 · 管理员不能审自己的菜")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe

        admin = ctx.auth.register("admin", "password3", "管理员")["user"]
        dish_id = svc.create(admin, dict(SAMPLE))["id"]
        svc.submit_review(admin, dish_id)

        _expect_error(
            lambda: svc.review(admin, dish_id, True),
            RecipeForbidden,
            "管理员审核自己的菜被拒",
            "不能审核自己",
        )
        # 管理员自己的菜仍可按普通用户方式维护
        check("管理员也能建个人菜谱", svc.get(admin, dish_id)["status"] == "pending")


# ── 服务层：下架 / 恢复 / 删除 ──────────────────────────────────

def test_archive_and_history() -> None:
    section("服务层 · 下架与历史菜单")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe

        alice = ctx.auth.register("alice", "password1", "小A")["user"]
        family_id = alice["familyId"]

        dish_id = svc.create(alice, dict(SAMPLE))["id"]

        # 下架前：橱窗可见，且能加入菜单
        check("下架前橱窗可见",
              any(i["id"] == dish_id for i in ctx.menu.list_dishes(user_id=alice["id"])["items"]))
        ctx.order.add_item(family_id, dish_id, "mon", "lunch")
        menu = ctx.order.get_week(family_id)
        check("下架前菜单有 1 项", menu["totals"]["items"] == 1)

        archived = svc.archive(alice, dish_id)
        check("下架后状态为 archived", archived["status"] == "archived")
        check("下架后状态标签为「已下架」", archived["statusLabel"] == "已下架")

        # 下架后：橱窗消失，但历史菜单仍在
        check("下架后橱窗不可见",
              not any(i["id"] == dish_id for i in ctx.menu.list_dishes(user_id=alice["id"])["items"]))
        menu_after = ctx.order.get_week(family_id)
        check("下架后历史菜单仍展示", menu_after["totals"]["items"] == 1)
        mon_lunch = next(d for d in menu_after["days"] if d["key"] == "mon")["meals"]["lunch"]
        check("历史菜单菜品名正常", mon_lunch["items"][0]["baseName"] == SAMPLE["name"])

        # 下架后仍能在"我的菜谱"里看到
        check("下架后我的菜谱里仍在",
              any(i["id"] == dish_id for i in svc.list_visible(alice)["items"]))
        _expect_error(lambda: svc.archive(alice, dish_id), RecipeError, "重复下架被拒", "已经是下架")
        check("下架后不可提交审核", archived["canSubmit"] is False)
        check("下架后可以恢复", archived["canRestore"] is True)

        # 恢复
        restored = svc.restore(alice, dish_id)
        check("恢复后状态为 private", restored["status"] == "private")
        check("恢复后橱窗重新可见",
              any(i["id"] == dish_id for i in ctx.menu.list_dishes(user_id=alice["id"])["items"]))
        _expect_error(
            lambda: svc.restore(alice, dish_id), RecipeError, "未下架的不能恢复", "只有已下架"
        )

        # public 的菜谱不能下架
        _expect_error(
            lambda: svc.archive(alice, "mapo-tofu"), RecipeForbidden, "公共菜谱不可下架"
        )


def test_delete() -> None:
    section("服务层 · 删除")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe

        alice = ctx.auth.register("alice", "password1", "小A")["user"]
        family_id = alice["familyId"]

        # 未被引用的：可以物理删除
        free_id = svc.create(alice, {**SAMPLE, "name": "没人点的菜"})["id"]
        result = svc.delete(alice, free_id)
        check("未被引用可物理删除", result["deleted"] is True)
        check("删除后数据真的没了", repo.get_recipe(free_id) is None)
        _expect_error(lambda: svc.get(alice, free_id), RecipeNotFound, "删除后读取 404")

        # 被菜单引用的：拒绝删除
        used_id = svc.create(alice, {**SAMPLE, "name": "已被排进菜单的菜"})["id"]
        ctx.order.add_item(family_id, used_id, "tue", "dinner")
        _expect_error(
            lambda: svc.delete(alice, used_id),
            RecipeError,
            "被菜单引用的菜谱拒绝删除",
            "不能删除",
        )
        check("拒绝后数据仍在", repo.get_recipe(used_id) is not None)

        # 待审核的不能删
        pending_id = svc.create(alice, {**SAMPLE, "name": "审核中的菜"})["id"]
        svc.submit_review(alice, pending_id)
        _expect_error(
            lambda: svc.delete(alice, pending_id),
            RecipeError,
            "待审核的菜谱不能直接删",
            "请先撤回",
        )

        # 删除时同步清理收藏
        fav_id = svc.create(alice, {**SAMPLE, "name": "被收藏的菜"})["id"]
        ctx.favorite.add(alice["id"], fav_id)
        check("收藏生效", ctx.favorite.list(alice["id"])["total"] == 1)
        svc.delete(alice, fav_id)
        check("删除后收藏被清理", ctx.favorite.list(alice["id"])["total"] == 0)


# ── 服务层：参数校验 ────────────────────────────────────────────

def test_validation() -> None:
    section("服务层 · 参数校验")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        svc = ctx.recipe
        alice = ctx.auth.register("alice", "password1", "小A")["user"]

        def bad(payload, keyword):
            return lambda: svc.create(alice, payload)

        _expect_error(bad({**SAMPLE, "name": ""}, "名称"), RecipeError, "名称为空被拒", "不能为空")
        _expect_error(
            bad({**SAMPLE, "name": "长" * 31}, "名称"), RecipeError, "名称超 30 字被拒", "最多"
        )
        _expect_error(
            bad({**SAMPLE, "name": "  "}, "名称"), RecipeError, "名称全空白被拒", "不能为空"
        )
        _expect_error(
            bad({**SAMPLE, "time": 0}, "时长"), RecipeError, "时长为 0 被拒", "大于 0"
        )
        _expect_error(
            bad({**SAMPLE, "time": -5}, "时长"), RecipeError, "时长为负被拒", "大于 0"
        )
        _expect_error(
            bad({**SAMPLE, "time": "abc"}, "时长"), RecipeError, "时长非数字被拒", "大于 0"
        )
        _expect_error(
            bad({**SAMPLE, "ingredients": []}, "食材"), RecipeError, "食材为空被拒", "至少需要 1 项食材"
        )
        _expect_error(
            bad({**SAMPLE, "ingredients": [{"name": "", "amount": "1"}]}, "食材"),
            RecipeError,
            "食材名称为空被过滤后判空",
            "至少需要 1 项食材",
        )
        _expect_error(
            bad({**SAMPLE, "steps": []}, "步骤"), RecipeError, "步骤为空被拒", "至少需要 1 个"
        )
        _expect_error(
            bad({**SAMPLE, "difficulty": "地狱难度"}, "难度"), RecipeError, "非法难度被拒", "难度只能是"
        )

        # 标签：非法值被静默丢弃，合法值保留
        ok = svc.create(alice, {**SAMPLE, "tags": ["veg", "不存在的标签", "spicy", "veg"]})
        check("非法标签被过滤", ok["tags"] == ["veg", "spicy"], str(ok["tags"]))
        check("空标签允许", svc.create(alice, {**SAMPLE, "tags": []})["tags"] == [])

        # 时长取整、超限截断
        rounded = svc.create(alice, {**SAMPLE, "time": 12.7})
        check("时长小数取整", rounded["time"] == 13, str(rounded["time"]))
        capped = svc.create(alice, {**SAMPLE, "time": 99999})
        check("时长上限 1440", capped["time"] == 1440, str(capped["time"]))

        # 营养缺项补 0
        partial = svc.create(alice, {**SAMPLE, "nutrition": {"calorie": 100}})
        check("营养缺项补 0", partial["nutrition"]["protein"] == 0 and partial["nutrition"]["calorie"] == 100)

        # 名称首尾空白被清理
        trimmed = svc.create(alice, {**SAMPLE, "name": "  带空白的名字  "})
        check("名称首尾空白被清理", trimmed["name"] == "带空白的名字")


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


def test_api_recipes() -> None:
    section("API 层 · 菜谱接口")
    with tempfile.TemporaryDirectory() as tmp:
        repo = bootstrap(Path(tmp))
        ctx = build_context(repo)
        server = create_server("127.0.0.1", 0, ctx, quiet=True)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            # 三个账号：普通作者、旁观者、管理员
            _, p = _request(port, "POST", "/api/auth/register",
                            {"username": "author", "password": "password1", "displayName": "作者"})
            token_a = p["data"]["token"]
            author_id = p["data"]["user"]["id"]

            _, p = _request(port, "POST", "/api/auth/register",
                            {"username": "viewer", "password": "password2", "displayName": "旁观者"})
            token_b = p["data"]["token"]

            _, p = _request(port, "POST", "/api/auth/register",
                            {"username": "admin", "password": "password3", "displayName": "管理员"})
            token_admin = p["data"]["token"]

            # 未登录 401
            status, _ = _request(port, "GET", "/api/recipes")
            check("未登录访问菜谱接口 401", status == 401)

            # 初始列表
            status, p = _request(port, "GET", "/api/recipes", token=token_a)
            check("GET /api/recipes 200", status == 200 and p["ok"] is True)
            check("初始含 39 道公共菜谱", p["data"]["counts"]["public"] == 39,
                  str(p["data"]["counts"]))
            check("普通用户 isReviewer 为假", p["data"]["isReviewer"] is False)
            check("列表项字段齐全",
                  {"id", "name", "status", "statusLabel", "ownerId", "isMine", "canEdit",
                   "canSubmit", "canReview"} <= set(p["data"]["items"][0]))

            # 新增
            status, p = _request(port, "POST", "/api/recipes", SAMPLE, token=token_a)
            check("POST 新增菜谱 200", status == 200 and p["ok"] is True)
            dish_id = p["data"]["id"]
            check("新增返回 private", p["data"]["status"] == "private")
            check("新增带完整详情", len(p["data"]["ingredients"]) == 3)

            # 缺字段 400
            status, p = _request(port, "POST", "/api/recipes", {"name": ""}, token=token_a)
            check("缺名称返回 400", status == 400 and p["ok"] is False)
            status, p = _request(port, "POST", "/api/recipes", None, token=token_a)
            check("空 body 返回 400", status == 400)

            # 详情
            status, p = _request(port, "GET", f"/api/recipes/{dish_id}", token=token_a)
            check("GET 菜谱详情 200", status == 200 and p["data"]["id"] == dish_id)
            # 他人读私人菜谱 404
            status, p = _request(port, "GET", f"/api/recipes/{dish_id}", token=token_b)
            check("他人读私人菜谱 404", status == 404)

            # 修改
            status, p = _request(port, "PATCH", f"/api/recipes/{dish_id}",
                                 {"subtitle": "改过的副标题"}, token=token_a)
            check("PATCH 修改 200", status == 200 and p["data"]["subtitle"] == "改过的副标题")
            status, p = _request(port, "PATCH", f"/api/recipes/{dish_id}",
                                 {"name": "别人改的"}, token=token_b)
            check("他人修改 403", status == 403)
            status, p = _request(port, "PATCH", "/api/recipes/mapo-tofu",
                                 {"name": "改内置"}, token=token_a)
            check("改公共菜谱 403", status == 403)

            # 待审核接口权限
            status, p = _request(port, "GET", "/api/recipes/pending", token=token_b)
            check("非审核员看待审核 403", status == 403)
            status, p = _request(port, "GET", "/api/recipes/pending", token=token_admin)
            check("审核员看待审核 200", status == 200 and p["ok"] is True)

            # 提交 → 待审核列表出现
            status, p = _request(port, "POST", f"/api/recipes/{dish_id}/submit", token=token_a)
            check("POST 提交审核 200", status == 200 and p["data"]["status"] == "pending")
            status, p = _request(port, "GET", "/api/recipes/pending", token=token_admin)
            check("待审核列表出现该菜谱",
                  status == 200 and any(i["id"] == dish_id for i in p["data"]["items"]))

            # 撤回
            status, p = _request(port, "POST", f"/api/recipes/{dish_id}/withdraw", token=token_a)
            check("POST 撤回审核 200", status == 200 and p["data"]["status"] == "private")

            # 再提交，管理员通过
            _request(port, "POST", f"/api/recipes/{dish_id}/submit", token=token_a)
            status, p = _request(port, "POST", f"/api/recipes/{dish_id}/review",
                                 {"approve": True, "note": "不错"}, token=token_admin)
            check("POST 审核通过 200", status == 200 and p["data"]["status"] == "public")
            check("通过后归属仍是作者", p["data"]["ownerId"] == author_id)

            status, p = _request(port, "GET", f"/api/recipes/{dish_id}", token=token_b)
            check("通过后他人可读", status == 200 and p["data"]["status"] == "public")

            # 审核参数校验
            status, p = _request(port, "POST", f"/api/recipes/{dish_id}/review",
                                 {"approve": True}, token=token_admin)
            check("已审核过的再审核 400", status == 400)
            status, p = _request(port, "POST", f"/api/recipes/{dish_id}/review",
                                 {"note": "缺 approve"}, token=token_admin)
            check("缺少 approve 参数 400", status == 400 and "approve" in p["error"])

            # 驳回流程（新菜谱）
            status, p = _request(port, "POST", "/api/recipes",
                                 {**SAMPLE, "name": "待驳回的菜"}, token=token_a)
            reject_id = p["data"]["id"]
            _request(port, "POST", f"/api/recipes/{reject_id}/submit", token=token_a)
            status, p = _request(port, "POST", f"/api/recipes/{reject_id}/review",
                                 {"approve": False, "note": "图片太糊"}, token=token_admin)
            check("POST 驳回 200", status == 200 and p["data"]["status"] == "rejected")
            check("驳回原因已记录", p["data"]["reviewNote"] == "图片太糊")

            # 下架 / 恢复
            status, p = _request(port, "POST", f"/api/recipes/{reject_id}/archive", token=token_a)
            check("POST 下架 200", status == 200 and p["data"]["status"] == "archived")
            status, p = _request(port, "POST", f"/api/recipes/{reject_id}/restore", token=token_a)
            check("POST 恢复 200", status == 200 and p["data"]["status"] == "private")

            # 删除：被引用拒绝 / 未被引用允许
            status, p = _request(port, "POST", "/api/recipes",
                                 {**SAMPLE, "name": "要删的菜"}, token=token_a)
            del_id = p["data"]["id"]
            _request(port, "POST", "/api/menu/items",
                     {"dishId": del_id, "day": "mon", "meal": "lunch"}, token=token_a)
            status, p = _request(port, "DELETE", f"/api/recipes/{del_id}", token=token_a)
            check("被菜单引用时删除 400", status == 400 and "不能删除" in p["error"])

            status, p = _request(port, "POST", "/api/recipes",
                                 {**SAMPLE, "name": "自由删的菜"}, token=token_a)
            free_id = p["data"]["id"]
            status, p = _request(port, "DELETE", f"/api/recipes/{free_id}", token=token_a)
            check("未被引用时可删除 200", status == 200 and p["data"]["deleted"] is True)

            # 越权删除
            status, p = _request(port, "POST", "/api/recipes",
                                 {**SAMPLE, "name": "别人的菜"}, token=token_a)
            other_id = p["data"]["id"]
            status, p = _request(port, "DELETE", f"/api/recipes/{other_id}", token=token_b)
            check("他人删除 403", status == 403)

            # 点餐橱窗可见性
            status, p = _request(port, "GET", "/api/dishes", token=token_b)
            viewer_total = p["data"]["total"]
            status, p = _request(port, "GET", "/api/dishes", token=token_a)
            check("橱窗：作者能看到自己的私人菜谱",
                  p["data"]["total"] > viewer_total,
                  f"author={p['data']['total']} viewer={viewer_total}")

            # 不存在的菜谱详情
            status, _ = _request(port, "GET", "/api/recipes/r_ffffffffffff", token=token_a)
            check("不存在的菜谱 404", status == 404)

            # 无敏感字段外泄
            status, p = _request(port, "GET", "/api/recipes", token=token_a)
            blob = json.dumps(p, ensure_ascii=False)
            check("响应不含密码哈希", "passwordHash" not in blob and "salt" not in blob)
        finally:
            server.shutdown()
            server.server_close()


def main() -> int:
    print("=" * 60)
    print("  菜谱维护与审核体系自测")
    print("=" * 60)
    test_create_and_isolation()
    test_public_recipe_readonly()
    test_review_flow()
    test_reject_flow()
    test_withdraw()
    test_admin_cannot_review_self()
    test_archive_and_history()
    test_delete()
    test_validation()
    test_api_recipes()

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
