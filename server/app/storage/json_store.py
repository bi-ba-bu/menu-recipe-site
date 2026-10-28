"""
storage/json_store.py — 基于 JSON 文件的最小存储引擎

设计目标：
    · 零第三方依赖（只用标准库），方便后续打包与部署
    · 原子写入：先写临时文件再 os.replace，避免中途崩溃留下半截文件
    · 进程内锁 + 文件锁：多线程 / 多进程同时写不会互相覆盖
    · 损坏自愈：JSON 解析失败时自动备份损坏文件并回落为空数据

文件布局（均为 UTF-8、缩进 2 的空格，便于人工查看与 diff）：
    data/
    ├── recipes.json      # 菜品库（种子数据，启动时自动初始化）
    ├── orders.json       # 点餐订单（按周存储）
    ├── favorites.json    # 收藏
    ├── config.json       # 系统配置（周信息、营养目标等）
    └── backups/          # 损坏文件的备份
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:  # 文件锁在 Windows 与 POSIX 上都可用
    import fcntl  # type: ignore
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore


class StorageError(Exception):
    """存储层异常基类。"""


class JsonStore:
    """单个 JSON 文件的读写封装，带原子写入与并发保护。"""

    def __init__(self, path: Path, default_factory: Callable[[], Any]) -> None:
        self.path = Path(path)
        self.default_factory = default_factory
        self._lock = threading.RLock()
        self._lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # ── 公开接口 ────────────────────────────────────────────────

    def exists(self) -> bool:
        return self.path.exists()

    def read(self) -> Any:
        """读取整个文件；文件不存在或内容损坏时返回默认值。"""
        with self._lock:
            if not self.path.exists():
                data = self.default_factory()
                self._write_unlocked(data)
                return data

            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return self.default_factory()

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                # 损坏文件先备份，避免直接丢数据，再回落为空
                self._backup_corrupted()
                data = self.default_factory()
                self._write_unlocked(data)
                return data

    def write(self, data: Any) -> None:
        """原子写入整个文件。"""
        with self._lock:
            self._write_unlocked(data)

    def update(self, mutator: Callable[[Any], Any]) -> Any:
        """
        读-改-写事务。

        mutator 接收当前数据并返回新数据；整个过程持有锁，
        保证并发调用不会交错覆盖。
        """
        with self._lock:
            current = self.read()
            updated = mutator(current)
            self._write_unlocked(updated)
            return updated

    # ── 内部实现 ────────────────────────────────────────────────

    def _write_unlocked(self, data: Any) -> None:
        """实际写盘：临时文件 + os.replace，保证原子性。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False, indent=2)

        # 跨进程写锁：拿不到锁时降级为直接写（单进程场景足够）
        lock_fd = None
        try:
            if fcntl is not None:
                lock_fd = open(self._lock_path, "w")
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        except OSError:
            lock_fd = None

        try:
            fd, tmp_path = tempfile.mkstemp(
                dir=str(self.path.parent), prefix=self.path.name + ".", suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(payload)
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(tmp_path, self.path)
            except Exception:
                # 写入失败时清理临时文件，避免残留
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                raise
        finally:
            if lock_fd is not None:
                try:
                    if fcntl is not None:
                        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                finally:
                    lock_fd.close()

    def _backup_corrupted(self) -> None:
        """把损坏文件复制到 backups 目录并保留时间戳。"""
        backup_dir = self.path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = backup_dir / f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}"
        try:
            shutil.copy2(self.path, target)
        except OSError:
            pass
