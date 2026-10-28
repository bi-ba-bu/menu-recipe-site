"""
services/family_service.py — 家庭管理

模型：
    · 一个用户可加入多个家庭（多对多）
    · 每个家庭有且只有一个家长（owner），家长可管理成员
    · 注册时自动创建"自己的家庭"，用户即为家长
    · 用户可在多个家庭间切换，当前家庭记录在会话里
    · 菜单挂在家庭上 → 切到哪个家庭，看到的就是那个家庭的菜单
    · 收藏挂在用户上 → 无论切到哪个家庭，收藏都是自己的

权限矩阵：
                    家长(owner)     成员(member)
    查看家庭信息         ✓               ✓
    切换进入家庭         ✓(自己建的)      ✓
    生成/重置邀请码      ✓               ✗
    移除成员             ✓               ✗
    重命名家庭           ✓               ✗
    解散家庭             ✓（仅自己建的）  ✗
    参与菜单管理         ✓               ✓
    退出家庭             ✗（需解散）      ✓
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from ..storage.repository import Repository


class FamilyError(Exception):
    """家庭业务异常，message 可直接展示给用户。"""


# 邀请码字符集：去掉易混淆的 0/O/1/I/L
_INVITE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_INVITE_LEN = 6

MAX_MEMBERS = 20
MAX_FAMILY_NAME = 20


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gen_invite_code(repo: Repository) -> str:
    """生成不与现有家庭冲突的邀请码。"""
    for _ in range(20):
        code = "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(_INVITE_LEN))
        if repo.find_family_by_invite_code(code) is None:
            return code
    # 极端情况下退化为更长的码，保证唯一
    return "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(_INVITE_LEN + 4))


class FamilyService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    # ── 内部 ────────────────────────────────────────────────────

    def _require_family(self, family_id: str) -> dict[str, Any]:
        family = self.repo.get_family(family_id)
        if family is None:
            raise FamilyError("家庭不存在")
        return family

    def _member_ids(self, family: dict[str, Any]) -> list[str]:
        """家庭成员列表，家长始终算作成员且排第一。"""
        owner = family.get("ownerId", "")
        members = [m for m in (family.get("members") or []) if m != owner]
        return ([owner] if owner else []) + members

    def is_owner(self, family: dict[str, Any], user_id: str) -> bool:
        return family.get("ownerId") == user_id

    def is_member(self, family: dict[str, Any], user_id: str) -> bool:
        return user_id in self._member_ids(family)

    def _require_owner(self, family: dict[str, Any], user_id: str) -> None:
        if not self.is_owner(family, user_id):
            raise FamilyError("只有家长可以进行此操作")

    def family_view(self, family: dict[str, Any], viewer_id: str) -> dict[str, Any]:
        """家庭详情：成员信息 + 当前用户在该家庭中的角色。"""
        owner_id = family.get("ownerId", "")
        members = []
        for member_id in self._member_ids(family):
            user = self.repo.get_user(member_id)
            if user is None:
                continue
            members.append(
                {
                    "id": user.get("id", ""),
                    "username": user.get("username", ""),
                    "displayName": user.get("displayName", ""),
                    "role": "owner" if member_id == owner_id else "member",
                    "isMe": member_id == viewer_id,
                }
            )

        owner_user = self.repo.get_user(owner_id) or {}
        role = "owner" if owner_id == viewer_id else "member"
        return {
            "id": family.get("id", ""),
            "name": family.get("name", ""),
            "ownerId": owner_id,
            "ownerName": owner_user.get("displayName") or owner_user.get("username") or "",
            "members": members,
            "memberCount": len(members),
            "createdAt": family.get("createdAt", ""),
            "role": role,
            "isOwner": role == "owner",
            # 邀请码只对家长可见，避免成员随意拉人
            "inviteCode": family.get("inviteCode", "") if role == "owner" else "",
            "isSelfCreated": owner_id == viewer_id,
        }

    def list_my_families(self, user_id: str, current_family_id: str = "") -> dict[str, Any]:
        """用户可切换的家庭列表（带当前标记）。"""
        families = self.repo.list_families_of_user(user_id)
        items = []
        for family in families:
            owner_user = self.repo.get_user(family.get("ownerId", "")) or {}
            items.append(
                {
                    "id": family.get("id", ""),
                    "name": family.get("name", ""),
                    "ownerName": owner_user.get("displayName") or owner_user.get("username") or "",
                    "role": "owner" if family.get("ownerId") == user_id else "member",
                    "memberCount": len(self._member_ids(family)),
                    "isActive": family.get("id") == current_family_id,
                }
            )
        return {"items": items, "total": len(items), "activeFamilyId": current_family_id}

    def create_family(self, owner_id: str, name: str) -> dict[str, Any]:
        """用户自建一个家庭，自己成为家长。"""
        clean_name = (name or "").strip()
        if not clean_name:
            raise FamilyError("请输入家庭名称")
        if len(clean_name) > MAX_FAMILY_NAME:
            raise FamilyError(f"家庭名称最多 {MAX_FAMILY_NAME} 个字")

        # 防止重名带来困惑（同一家长下不允许重名）
        for family in self.repo.list_families_of_user(owner_id):
            if family.get("ownerId") == owner_id and family.get("name") == clean_name:
                raise FamilyError("你已经有一个同名家庭了")

        family = {
            "id": f"f_{uuid.uuid4().hex[:12]}",
            "name": clean_name,
            "ownerId": owner_id,
            "members": [owner_id],
            "inviteCode": _gen_invite_code(self.repo),
            "createdAt": _now_iso(),
        }
        self.repo.create_family(family)
        return self.family_view(family, owner_id)

    def join_by_code(self, user_id: str, code: str) -> dict[str, Any]:
        """凭邀请码加入家庭。"""
        family = self.repo.find_family_by_invite_code(code)
        if family is None:
            raise FamilyError("邀请码无效，请确认后重试")

        family_id = family.get("id", "")
        if self.is_member(family, user_id):
            raise FamilyError("你已经在这个家庭里了")

        if len(self._member_ids(family)) >= MAX_MEMBERS:
            raise FamilyError(f"该家庭人数已满（上限 {MAX_MEMBERS} 人）")

        self.repo.add_family_member(family_id, user_id)
        family = self.repo.get_family(family_id) or family
        return self.family_view(family, user_id)

    def remove_member(self, family_id: str, operator_id: str, target_id: str) -> dict[str, Any]:
        """家长移除成员。"""
        family = self._require_family(family_id)
        self._require_owner(family, operator_id)

        if target_id == family.get("ownerId"):
            raise FamilyError("家长不能移除自己，如需退出请解散家庭")
        if not self.is_member(family, target_id):
            raise FamilyError("该用户不在此家庭中")

        self.repo.remove_family_member(family_id, target_id)
        family = self.repo.get_family(family_id) or family
        return self.family_view(family, operator_id)

    def leave_family(self, family_id: str, user_id: str) -> dict[str, Any]:
        """成员主动退出家庭。家长不能退出（需先解散或转让）。"""
        family = self._require_family(family_id)
        if self.is_owner(family, user_id):
            raise FamilyError("家长不能退出自己的家庭，如需删除请解散家庭")
        if not self.is_member(family, user_id):
            raise FamilyError("你不在此家庭中")

        self.repo.remove_family_member(family_id, user_id)
        return {"left": True, "familyId": family_id}

    def rename_family(self, family_id: str, operator_id: str, name: str) -> dict[str, Any]:
        family = self._require_family(family_id)
        self._require_owner(family, operator_id)

        clean_name = (name or "").strip()
        if not clean_name:
            raise FamilyError("请输入家庭名称")
        if len(clean_name) > MAX_FAMILY_NAME:
            raise FamilyError(f"家庭名称最多 {MAX_FAMILY_NAME} 个字")

        updated = self.repo.update_family(family_id, {"name": clean_name})
        return self.family_view(updated or family, operator_id)

    def reset_invite_code(self, family_id: str, operator_id: str) -> dict[str, Any]:
        family = self._require_family(family_id)
        self._require_owner(family, operator_id)
        code = _gen_invite_code(self.repo)
        updated = self.repo.update_family(family_id, {"inviteCode": code})
        return self.family_view(updated or family, operator_id)

    def dissolve_family(self, family_id: str, user_id: str) -> dict[str, Any]:
        """
        解散家庭（仅家长可操作）。

        允许多次解散，但每个用户必须至少保留一个自己当家长的家庭，
        否则就会出现"无家可归"的账号，菜单也无处挂载。
        """
        family = self._require_family(family_id)
        self._require_owner(family, user_id)

        owned = [f for f in self.repo.list_families_of_user(user_id) if f.get("ownerId") == user_id]
        if len(owned) <= 1:
            raise FamilyError("你至少需要保留一个自己创建的家庭")

        self.repo.delete_family(family_id)
        return {"dissolved": True, "familyId": family_id}

    def resolve_active_family(self, user: dict[str, Any], current_family_id: str) -> dict[str, Any]:
        """
        确定用户当前应当使用的家庭。

        优先级：
            1. 会话里记录的家庭（用户上次切换到的）
            2. 用户自己创建的家庭
            3. 任意一个已加入的家庭
        账号若一个家庭都没有（历史数据），自动补建一个。
        """
        families = self.repo.list_families_of_user(user.get("id", ""))
        if not families:
            created = self.create_family(user.get("id", ""), f"{user.get('displayName', '我')}的家庭")
            families = self.repo.list_families_of_user(user.get("id", ""))

        # 会话里的家庭必须仍然有效（可能已被移除/解散）
        if current_family_id:
            for family in families:
                if family.get("id") == current_family_id:
                    return family

        return families[0]
