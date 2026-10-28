"""
app/__init__.py — 应用装配

把存储层、服务层、API 层组装成可直接启动的应用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .api.router import AppContext, create_server
from .seed import RECIPES
from .storage.json_store import JsonStore
from .storage.repository import RECIPE_STATUS_PUBLIC, Repository

# 项目根：menu-recipe-site/
SITE_ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_ROOT = SITE_ROOT / "server"
DEFAULT_DATA_DIR = SERVER_ROOT / "data"


def bootstrap(data_dir: Path | None = None) -> Repository:
    """
    初始化仓库。

    首次启动时把 seed.py 里的菜品库写入 recipes.json，
    之后以文件为准（允许通过接口或手工编辑维护）。

    菜谱归属模型（v2）：
        · 种子菜谱（39 道）归属系统，status = public（公共菜谱）
        · 用户新增菜谱归属本人，status = private（个人菜谱）
        · 个人菜谱可提交审核 → pending，管理员通过后变 public
        · 下架：status = archived，不再出现在点餐列表，但历史菜单不受影响
    """
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    repo = Repository(data_dir)

    # 菜品库种子化：文件缺失或为空时用内置数据初始化
    store = JsonStore(repo.recipes.path, dict)
    current = store.read()

    # 给种子数据打上归属与状态标记（幂等：已有字段不覆盖）
    seeded: dict[str, Any] = {}
    for dish_id, recipe in RECIPES.items():
        seeded[dish_id] = {
            **recipe,
            "ownerId": "system",
            "status": RECIPE_STATUS_PUBLIC,
            "origin": "seed",
        }

    if not current:
        store.write(seeded)
    else:
        # 增量补齐：种子里有、文件里缺的菜品自动补上
        missing = {k: v for k, v in seeded.items() if k not in current}
        # 老数据补字段：v1 没有 ownerId/status 的，视为系统公共菜谱
        patched = {}
        for dish_id, recipe in current.items():
            if "status" not in recipe:
                patched[dish_id] = {
                    "ownerId": "system",
                    "status": RECIPE_STATUS_PUBLIC,
                    "origin": "seed",
                    "reviewNote": "",
                    **recipe,
                }
        if missing or patched:
            store.write({**current, **patched, **missing})

    return repo


def build_context(repo: Repository, static_dir: Path | None = None) -> AppContext:
    return AppContext(repo, static_dir or SITE_ROOT)


def serve(
    host: str = "127.0.0.1",
    port: int = 5188,
    data_dir: Path | None = None,
    static_dir: Path | None = None,
    quiet: bool = False,
):
    """创建 HTTP 服务器（未启动）。"""
    repo = bootstrap(data_dir)
    ctx = build_context(repo, static_dir)
    return create_server(host, port, ctx, quiet=quiet)
