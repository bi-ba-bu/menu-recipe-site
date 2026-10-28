"""
services/auth_service.py — 注册、登录与会话

安全设计（全部使用标准库）：
    · 密码用 PBKDF2-HMAC-SHA256 + 每用户随机盐，迭代 20 万次
    · 数据库里绝不出现明文密码，也不返回任何密码字段
    · 会话用 secrets 生成的高熵 token，存服务端，可随时撤销
    · 会话带过期时间，默认 30 天，过期自动失效并清理
    · 登录失败统一提示"用户名或密码错误"，不泄露账号是否存在（防枚举）
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from ..storage.repository import Repository

# 密码策略
MIN_PASSWORD_LEN = 6
MAX_PASSWORD_LEN = 128
MIN_USERNAME_LEN = 2
MAX_USERNAME_LEN = 24

# PBKDF2 迭代次数：兼顾安全与纯 Python 下的响应速度
PBKDF2_ITERATIONS = 200_000

# 会话有效期
SESSION_DAYS = 30


class AuthError(Exception):
    """认证相关异常，message 可直接展示给用户。"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _hash_password(password: str, salt: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    """PBKDF2-HMAC-SHA256 派生密码哈希（十六进制）。"""
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return digest.hex()


def _verify_password(password: str, salt: str, expected: str, iterations: int) -> bool:
    """常量时间比较，避免时序攻击。"""
    actual = _hash_password(password, salt, iterations)
    return hmac.compare_digest(actual, expected)


class AuthService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    # ── 校验 ────────────────────────────────────────────────────

    def _validate_username(self, username: str) -> str:
        name = (username or "").strip()
        if len(name) < MIN_USERNAME_LEN:
            raise AuthError(f"用户名至少 {MIN_USERNAME_LEN} 个字符")
        if len(name) > MAX_USERNAME_LEN:
            raise AuthError(f"用户名最多 {MAX_USERNAME_LEN} 个字符")
        # 只允许中英文、数字、下划线与连字符，避免奇怪字符
        for ch in name:
            if not (ch.isalnum() or ch in "_-"):
                raise AuthError("用户名只能包含中英文、数字、下划线和连字符")
        return name

    def _validate_password(self, password: str) -> str:
        pwd = password or ""
        if len(pwd) < MIN_PASSWORD_LEN:
            raise AuthError(f"密码至少 {MIN_PASSWORD_LEN} 位")
        if len(pwd) > MAX_PASSWORD_LEN:
            raise AuthError(f"密码最多 {MAX_PASSWORD_LEN} 位")
        return pwd

    # ── 注册 ────────────────────────────────────────────────────

    def register(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        """
        注册新账号。

        注册时自动创建"xxx 的家庭"，用户即为该家庭的家长。
        用户还可以凭邀请码加入其他家庭，因此家庭归属是多对多的。
        """
        name = self._validate_username(username)
        pwd = self._validate_password(password)

        if self.repo.find_user_by_username(name) is not None:
            raise AuthError("该用户名已被注册")

        user_id = f"u_{uuid.uuid4().hex[:12]}"
        family_id = f"f_{uuid.uuid4().hex[:12]}"
        salt = secrets.token_hex(16)
        now = _now()

        from .family_service import FamilyService  # 延迟导入避免循环依赖

        user = {
            "id": user_id,
            "username": name,
            "displayName": (display_name or name).strip()[:24],
            "passwordHash": _hash_password(pwd, salt),
            "salt": salt,
            "iterations": PBKDF2_ITERATIONS,
            # 默认家庭（自己当家长），用户可再加入其他家庭
            "familyId": family_id,
            "createdAt": _iso(now),
        }
        self.repo.create_user(user)

        families = FamilyService(self.repo)
        families.create_family(user_id, f"{user['displayName']}的家庭")

        token = self._issue_session(user_id, family_id)
        return {"token": token, "user": self._public_user(user, family_id)}

    # ── 登录 ────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> dict[str, Any]:
        user = self.repo.find_user_by_username(username or "")
        # 账号不存在与密码错误返回同一提示，避免账号枚举
        if user is None:
            raise AuthError("用户名或密码错误")

        if not _verify_password(
            password or "",
            user.get("salt", ""),
            user.get("passwordHash", ""),
            int(user.get("iterations", PBKDF2_ITERATIONS)),
        ):
            raise AuthError("用户名或密码错误")

        from .family_service import FamilyService  # 延迟导入避免循环依赖

        # 登录时恢复上次使用的家庭；没有则回落默认家庭
        families = FamilyService(self.repo)
        active = families.resolve_active_family(user, user.get("lastFamilyId", ""))
        token = self._issue_session(user["id"], active.get("id", ""))
        return {"token": token, "user": self._public_user(user, active.get("id", ""))}

    def logout(self, token: str) -> None:
        self.repo.delete_session(token)

    # ── 会话 ────────────────────────────────────────────────────

    def _issue_session(self, user_id: str, family_id: str = "") -> str:
        token = secrets.token_urlsafe(32)
        now = _now()
        # 顺带清理过期会话，避免文件无限增长
        self.repo.purge_expired_sessions(_iso(now))
        self.repo.save_session(
            token,
            {
                "userId": user_id,
                "currentFamilyId": family_id,
                "createdAt": _iso(now),
                "expiresAt": _iso(now + timedelta(days=SESSION_DAYS)),
            },
        )
        return token

    def resolve_token(self, token: str) -> dict[str, Any] | None:
        """token → 用户对象；无效或过期返回 None。"""
        if not token:
            return None
        session = self.repo.get_session(token)
        if session is None:
            return None
        if str(session.get("expiresAt", "")) <= _iso(_now()):
            # 过期即删除，不留无效会话
            self.repo.delete_session(token)
            return None
        user = self.repo.get_user(session.get("userId", ""))
        return user

    def get_session(self, token: str) -> dict[str, Any]:
        return self.repo.get_session(token) or {}

    def switch_family(self, token: str, user: dict[str, Any], family_id: str) -> dict[str, Any]:
        """
        切换当前家庭。

        权限：只要该用户属于目标家庭即可切换（家长与成员都可以）。
        切换后同时写入会话与用户资料，保证下次登录还记得。
        """
        from .family_service import FamilyError, FamilyService

        families = FamilyService(self.repo)
        family = self.repo.get_family(family_id)
        if family is None:
            raise FamilyError("家庭不存在")
        if not families.is_member(family, user.get("id", "")):
            raise FamilyError("你不在这个家庭中，无法切换")

        self.repo.update_session(token, {"currentFamilyId": family_id})
        self.repo.update_user(user.get("id", ""), {"lastFamilyId": family_id})
        return self._public_user({**user, "lastFamilyId": family_id}, family_id)

    # ── 用户信息 ────────────────────────────────────────────────

    def _public_user(self, user: dict[str, Any], active_family_id: str = "") -> dict[str, Any]:
        """
        对外暴露的用户信息：绝不包含密码哈希与盐。

        activeFamily 是当前正在使用的家庭；一个用户可能属于多个家庭，
        切换家庭后这里会随之变化。
        """
        from .family_service import FamilyService

        families = FamilyService(self.repo)
        family_id = active_family_id or user.get("familyId", "")
        family = self.repo.get_family(family_id) or {}

        # 兜底：当前家庭已失效时，重新解析一个可用家庭
        if not family:
            resolved = families.resolve_active_family(user, "")
            family = self.repo.get_family(resolved.get("id", "")) or {}
            family_id = family.get("id", "")

        role = "owner" if family.get("ownerId") == user.get("id") else "member"
        return {
            "id": user.get("id", ""),
            "username": user.get("username", ""),
            "displayName": user.get("displayName", ""),
            "familyId": family_id,
            "familyName": family.get("name", ""),
            "role": role,
            "familyCount": len(self.repo.list_families_of_user(user.get("id", ""))),
            "createdAt": user.get("createdAt", ""),
        }

    def current_user_info(self, user: dict[str, Any], active_family_id: str = "") -> dict[str, Any]:
        return self._public_user(user, active_family_id)
