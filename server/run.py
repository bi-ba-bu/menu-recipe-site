"""
run.py — 后端启动入口

用法：
    python server/run.py                    # 默认 127.0.0.1:5188
    python server/run.py --port 5190        # 换端口
    python server/run.py --host 0.0.0.0     # 允许局域网访问
    python server/run.py --reset            # 清空业务数据（保留菜品库）

同一端口同时提供：
    /            前端页面（静态文件）
    /api/*       后端接口
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# 允许 `python server/run.py` 与 `python -m server.run` 两种方式
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import DEFAULT_DATA_DIR, bootstrap, build_context  # noqa: E402
from app.api.router import create_server  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="今日食堂 · 菜单与食谱后端服务")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=5188, help="监听端口，默认 5188")
    parser.add_argument("--data-dir", default=None, help="数据目录，默认 server/data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="启动前清空订单与收藏（保留菜品库）",
    )
    parser.add_argument("--quiet", action="store_true", help="不打印每条请求日志")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR

    if args.reset:
        # 只清业务数据，菜品库与配置保留
        removed = []
        for name in (
            "orders.json",
            "favorites.json",
            "users.json",
            "sessions.json",
            "families.json",
        ):
            target = data_dir / name
            if target.exists():
                target.unlink()
                removed.append(name)
        backups = data_dir / "backups"
        if backups.exists():
            shutil.rmtree(backups)
            removed.append("backups/")
        print(f"已重置数据：{', '.join(removed) if removed else '无（本来就没有数据）'}")

    repo = bootstrap(data_dir)
    ctx = build_context(repo)
    server = create_server(args.host, args.port, ctx, quiet=args.quiet)

    url = f"http://{args.host}:{args.port}/"
    try:
        import socket

        hostname = socket.gethostname()
        lan_ip = socket.gethostbyname(hostname)
    except OSError:
        lan_ip = None

    print("=" * 56)
    print("  今日食堂 · 菜单与食谱服务已启动")
    print("=" * 56)
    print(f"  页面地址 : {url}")
    print(f"  接口地址 : {url}api/health")
    if args.host == "0.0.0.0" and lan_ip:
        print(f"  局域网   : http://{lan_ip}:{args.port}/")
    print(f"  数据目录 : {data_dir}")
    print(f"  菜品数量 : {len(repo.recipe_ids())}")
    print("  按 Ctrl+C 停止服务")
    print("=" * 56)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭服务…")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
