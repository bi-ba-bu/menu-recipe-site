"""
api/router.py — 极简路由与 HTTP 处理

不引入 Flask/FastAPI 等框架，只用标准库 http.server，原因：
    · 部署简单，python 直接跑，无 pip 依赖
    · 后续接入 AI 模块时，只需再加一个 /api/ai/* 前缀即可

同时承担：
    · 静态文件服务（前端 menu-recipe-site 目录）
    · 统一 JSON 响应与错误处理
    · CORS（便于前后端分离调试）
"""

from __future__ import annotations

import json
import mimetypes
import re
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlparse

from ..services.auth_service import AuthError, AuthService
from ..services.family_service import FamilyError, FamilyService
from ..services.favorite_service import FavoriteError, FavoriteService
from ..services.menu_service import MenuService
from ..services.order_service import OrderError, OrderService
from ..services.recipe_service import (
    RecipeError,
    RecipeForbidden,
    RecipeNotFound,
    RecipeService,
)


class ApiError(Exception):
    """带 HTTP 状态码的业务异常。"""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


# ── 路由表：(方法, 正则, 处理函数名, 是否需要登录) ──────────────
# 需要登录的接口会自动注入 user / family 上下文
#
# 正则里有两条容易踩坑的规则：
#   1. 命名组不能叫 family_id —— 分发器会额外注入 family_id 参数，重名会触发 TypeError
#   2. 静态路径段要写在同前缀的参数路由之前，否则 /api/recipes/pending
#      会被 /api/recipes/{dish_id} 抢先匹配成 dish_id="pending"
ROUTES: list[tuple[str, re.Pattern[str], str, bool]] = [
    # 公开接口：无需登录
    ("GET", re.compile(r"^/api/health$"), "health", False),
    ("POST", re.compile(r"^/api/auth/register$"), "register", False),
    ("POST", re.compile(r"^/api/auth/login$"), "login", False),
    # 登录态
    ("GET", re.compile(r"^/api/auth/me$"), "me", True),
    ("POST", re.compile(r"^/api/auth/logout$"), "logout", True),
    # 家庭管理
    ("GET", re.compile(r"^/api/families$"), "list_families", True),
    ("POST", re.compile(r"^/api/families$"), "create_family", True),
    ("GET", re.compile(r"^/api/families/(?P<target_family_id>[\w\-]+)$"), "family_detail", True),
    ("POST", re.compile(r"^/api/families/join$"), "join_family", True),
    ("POST", re.compile(r"^/api/families/(?P<target_family_id>[\w\-]+)/switch$"), "switch_family", True),
    ("PATCH", re.compile(r"^/api/families/(?P<target_family_id>[\w\-]+)$"), "rename_family", True),
    ("POST", re.compile(r"^/api/families/(?P<target_family_id>[\w\-]+)/invite-code$"), "reset_invite", True),
    ("POST", re.compile(r"^/api/families/(?P<target_family_id>[\w\-]+)/leave$"), "leave_family", True),
    (
        "DELETE",
        re.compile(r"^/api/families/(?P<target_family_id>[\w\-]+)/members/(?P<member_id>[\w\-]+)$"),
        "remove_member",
        True,
    ),
    ("DELETE", re.compile(r"^/api/families/(?P<target_family_id>[\w\-]+)$"), "dissolve_family", True),
    # 兼容旧路径：当前家庭信息
    ("GET", re.compile(r"^/api/family$"), "current_family", True),
    # 元数据与菜品（登录后可见）
    ("GET", re.compile(r"^/api/meta$"), "meta", True),
    ("GET", re.compile(r"^/api/dishes$"), "list_dishes", True),
    ("GET", re.compile(r"^/api/dishes/(?P<dish_id>[\w\-]+)$"), "dish_detail", True),
    # 菜谱维护与审核（个人菜谱 + 公共菜谱）
    # 注意：/api/recipes/pending 必须排在 /api/recipes/{dish_id} 之前
    ("GET", re.compile(r"^/api/recipes$"), "list_recipes", True),
    ("POST", re.compile(r"^/api/recipes$"), "create_recipe", True),
    ("GET", re.compile(r"^/api/recipes/pending$"), "list_pending_recipes", True),
    ("GET", re.compile(r"^/api/recipes/(?P<dish_id>[\w\-]+)$"), "recipe_detail", True),
    ("PATCH", re.compile(r"^/api/recipes/(?P<dish_id>[\w\-]+)$"), "update_recipe", True),
    ("DELETE", re.compile(r"^/api/recipes/(?P<dish_id>[\w\-]+)$"), "delete_recipe", True),
    ("POST", re.compile(r"^/api/recipes/(?P<dish_id>[\w\-]+)/archive$"), "archive_recipe", True),
    ("POST", re.compile(r"^/api/recipes/(?P<dish_id>[\w\-]+)/restore$"), "restore_recipe", True),
    ("POST", re.compile(r"^/api/recipes/(?P<dish_id>[\w\-]+)/submit$"), "submit_recipe", True),
    ("POST", re.compile(r"^/api/recipes/(?P<dish_id>[\w\-]+)/withdraw$"), "withdraw_recipe", True),
    ("POST", re.compile(r"^/api/recipes/(?P<dish_id>[\w\-]+)/review$"), "review_recipe", True),
    # 一周菜单 / 点餐（按家庭隔离）
    ("GET", re.compile(r"^/api/menu$"), "get_menu", True),
    ("POST", re.compile(r"^/api/menu/items$"), "add_item", True),
    ("PATCH", re.compile(r"^/api/menu/items$"), "set_quantity", True),
    ("DELETE", re.compile(r"^/api/menu/items$"), "remove_item", True),
    ("POST", re.compile(r"^/api/menu/generate$"), "generate_week", True),
    ("POST", re.compile(r"^/api/menu/clear$"), "clear_week", True),
    # 营养（按家庭隔离，菜单同源）
    ("GET", re.compile(r"^/api/nutrition$"), "get_nutrition", True),
    # 收藏（按用户隔离）
    ("GET", re.compile(r"^/api/favorites$"), "list_favorites", True),
    ("POST", re.compile(r"^/api/favorites$"), "add_favorite", True),
    ("DELETE", re.compile(r"^/api/favorites/(?P<dish_id>[\w\-]+)$"), "remove_favorite", True),
    ("POST", re.compile(r"^/api/favorites/(?P<dish_id>[\w\-]+)/toggle$"), "toggle_favorite", True),
]


class AppContext:
    """服务实例容器，供各 handler 使用。"""

    def __init__(self, repo, static_dir: Path) -> None:
        self.recipe = RecipeService(repo)
        self.menu = MenuService(repo)
        self.order = OrderService(repo)
        self.favorite = FavoriteService(repo)
        self.auth = AuthService(repo)
        self.family = FamilyService(repo)
        self.repo = repo
        self.static_dir = static_dir


class RequestHandler(BaseHTTPRequestHandler):
    """统一入口：先匹配 /api/*，未命中则当作静态资源。"""

    server_version = "MenuRecipeServer/1.0"
    ctx: AppContext  # 由 create_server 注入
    quiet: bool = False

    # ── HTTP 方法 ───────────────────────────────────────────────

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_PATCH(self) -> None:  # noqa: N802
        self._dispatch("PATCH")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch("DELETE")

    def do_PUT(self) -> None:  # noqa: N802
        # 未在路由表中声明，交给分发器统一返回 405（而不是默认的 501）
        self._dispatch("PUT")

    def do_OPTIONS(self) -> None:  # noqa: N802
        """CORS 预检。"""
        self.send_response(204)
        self._cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ── 分发 ────────────────────────────────────────────────────

    def _dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if not path.startswith("/api/"):
            self._serve_static(path)
            return

        for route_method, pattern, handler_name, need_auth in ROUTES:
            match = pattern.match(path)
            if not match:
                continue
            if route_method != method:
                continue

            handler: Callable[..., Any] = getattr(self, handler_name)
            try:
                body = self._read_json() if method in ("POST", "PATCH") else {}

                # 鉴权：需要登录的接口先解析 token，拿到当前用户与其当前家庭
                if need_auth:
                    user, family_id = self._require_context()
                    result = handler(
                        query=query,
                        body=body,
                        user=user,
                        family_id=family_id,
                        **match.groupdict(),
                    )
                else:
                    result = handler(query=query, body=body, **match.groupdict())
                self._send_json(200, {"ok": True, "data": result})
            except ApiError as exc:
                self._send_json(exc.status, {"ok": False, "error": exc.message})
            except (AuthError, FamilyError) as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
            except (OrderError, FavoriteError) as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
            except RecipeNotFound as exc:
                self._send_json(404, {"ok": False, "error": str(exc)})
            except RecipeForbidden as exc:
                self._send_json(403, {"ok": False, "error": str(exc)})
            except RecipeError as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:  # 兜底，避免单个请求打挂服务
                traceback.print_exc()
                self._send_json(500, {"ok": False, "error": f"服务器内部错误：{exc}"})
            return

        # 路径存在但方法不允许
        for route_method, pattern, _, _ in ROUTES:
            if pattern.match(path):
                self._send_json(405, {"ok": False, "error": f"不支持的请求方法：{method}"})
                return

        self._send_json(404, {"ok": False, "error": f"接口不存在：{path}"})

    # ── 鉴权 ────────────────────────────────────────────────────

    def _extract_token(self) -> str:
        """从 Authorization: Bearer <token> 或 X-Auth-Token 头取 token。"""
        header = self.headers.get("Authorization") or ""
        if header.lower().startswith("bearer "):
            return header[7:].strip()
        return (self.headers.get("X-Auth-Token") or "").strip()

    def _require_context(self) -> tuple[dict[str, Any], str]:
        """
        校验登录态并解析当前家庭。

        返回 (user, familyId)。familyId 决定菜单/营养的数据范围，
        收藏始终按 user.id 隔离，与当前家庭无关。
        """
        token = self._extract_token()
        user = self.ctx.auth.resolve_token(token) if token else None
        if user is None:
            raise ApiError(401, "登录已失效，请重新登录")

        session = self.ctx.auth.get_session(token)
        current = session.get("currentFamilyId", "")

        # 会话中的家庭可能已被移除/解散，服务层会做有效性校验与兜底
        family = self.ctx.family.resolve_active_family(user, current)
        family_id = family.get("id", "")

        # 兜底结果与会话不一致时顺手修正，避免每次都重新解析
        if family_id and family_id != current:
            self.ctx.repo.update_session(token, {"currentFamilyId": family_id})

        return user, family_id

    # ── 各接口实现 ──────────────────────────────────────────────

    def health(self, query, body) -> dict[str, Any]:
        return {"status": "ok", "dishCount": len(self.ctx.repo.recipe_ids())}

    # 公开：注册 / 登录
    def register(self, query, body) -> dict[str, Any]:
        username = body.get("username")
        password = body.get("password")
        if not username or not password:
            raise ApiError(400, "缺少参数：username / password")
        return self.ctx.auth.register(username, password, body.get("displayName"))

    def login(self, query, body) -> dict[str, Any]:
        username = body.get("username")
        password = body.get("password")
        if not username or not password:
            raise ApiError(400, "缺少参数：username / password")
        return self.ctx.auth.login(username, password)

    # 登录态
    def me(self, query, body, user, family_id) -> dict[str, Any]:
        return self.ctx.auth.current_user_info(user, family_id)

    def logout(self, query, body, user, family_id) -> dict[str, Any]:
        self.ctx.auth.logout(self._extract_token())
        return {"ok": True}

    # ── 家庭管理 ────────────────────────────────────────────────

    def list_families(self, query, body, user, family_id) -> dict[str, Any]:
        """我加入的全部家庭（供切换器使用）。"""
        return self.ctx.family.list_my_families(user.get("id", ""), family_id)

    def current_family(self, query, body, user, family_id) -> dict[str, Any]:
        """当前家庭的完整信息（兼容旧路径 /api/family）。"""
        family = self.ctx.repo.get_family(family_id)
        if family is None:
            raise FamilyError("家庭不存在")
        return self.ctx.family.family_view(family, user.get("id", ""))

    def family_detail(self, query, body, user, family_id, target_family_id: str = "") -> dict[str, Any]:
        target = target_family_id or family_id
        family = self.ctx.repo.get_family(target)
        if family is None:
            raise ApiError(404, "家庭不存在")
        if not self.ctx.family.is_member(family, user.get("id", "")):
            raise ApiError(403, "你不是该家庭的成员")
        return self.ctx.family.family_view(family, user.get("id", ""))

    def create_family(self, query, body, user, family_id) -> dict[str, Any]:
        name = body.get("name") or ""
        return self.ctx.family.create_family(user.get("id", ""), name)

    def join_family(self, query, body, user, family_id) -> dict[str, Any]:
        code = body.get("code") or ""
        if not code.strip():
            raise ApiError(400, "请输入邀请码")
        return self.ctx.family.join_by_code(user.get("id", ""), code)

    def switch_family(self, query, body, user, family_id, target_family_id: str = "") -> dict[str, Any]:
        target = target_family_id or body.get("familyId") or ""
        if not target:
            raise ApiError(400, "缺少参数：familyId")
        public_user = self.ctx.auth.switch_family(self._extract_token(), user, target)
        return {"user": public_user, "familyId": target}

    def rename_family(self, query, body, user, family_id, target_family_id: str = "") -> dict[str, Any]:
        target = target_family_id or family_id
        self._require_membership(target, user)
        return self.ctx.family.rename_family(target, user.get("id", ""), body.get("name") or "")

    def reset_invite(self, query, body, user, family_id, target_family_id: str = "") -> dict[str, Any]:
        target = target_family_id or family_id
        self._require_membership(target, user)
        return self.ctx.family.reset_invite_code(target, user.get("id", ""))

    def leave_family(self, query, body, user, family_id, target_family_id: str = "") -> dict[str, Any]:
        target = target_family_id or family_id
        self._require_membership(target, user)
        return self.ctx.family.leave_family(target, user.get("id", ""))

    def remove_member(
        self, query, body, user, family_id, target_family_id: str = "", member_id: str = ""
    ) -> dict[str, Any]:
        target = target_family_id or family_id
        self._require_membership(target, user)
        return self.ctx.family.remove_member(target, user.get("id", ""), member_id)

    def dissolve_family(self, query, body, user, family_id, target_family_id: str = "") -> dict[str, Any]:
        target = target_family_id or family_id
        self._require_membership(target, user)
        return self.ctx.family.dissolve_family(target, user.get("id", ""))

    def _require_membership(self, target_family_id: str, user: dict[str, Any]) -> None:
        """
        家庭操作的前置校验：必须是该家庭成员。

        非成员与"家庭不存在"返回同样的 403，
        避免通过状态码差异探测某个家庭 ID 是否存在。
        """
        family = self.ctx.repo.get_family(target_family_id)
        if family is None or not self.ctx.family.is_member(family, user.get("id", "")):
            raise ApiError(403, "你不是该家庭的成员")

    def meta(self, query, body, user, family_id) -> dict[str, Any]:
        return self.ctx.menu.get_meta()

    def list_dishes(self, query, body, user, family_id) -> dict[str, Any]:
        tag = (query.get("tag") or [None])[0]
        keyword = (query.get("q") or [None])[0]
        # 橱窗只展示当前用户可见的菜谱（公共 + 自己的），并剔除已下架
        return self.ctx.menu.list_dishes(tag=tag, q=keyword, user_id=user.get("id", ""))

    def dish_detail(self, query, body, user, family_id, dish_id: str) -> dict[str, Any]:
        data = self.ctx.menu.get_dish_detail(dish_id, user.get("id"))
        if data is None:
            raise ApiError(404, f"菜品不存在：{dish_id}")
        return data

    # ── 菜谱维护与审核 ──────────────────────────────────────────

    def list_recipes(self, query, body, user, family_id) -> dict[str, Any]:
        """
        我的菜谱 + 公共菜谱。

        查询参数：
            scope=public  只看公共菜谱（不带自己的私人菜谱）
        """
        scope = (query.get("scope") or [""])[0]
        include_own = scope != "public"
        return self.ctx.recipe.list_visible(user, include_own=include_own)

    def create_recipe(self, query, body, user, family_id) -> dict[str, Any]:
        return self.ctx.recipe.create(user, body)

    def recipe_detail(self, query, body, user, family_id, dish_id: str = "") -> dict[str, Any]:
        return self.ctx.recipe.get(user, dish_id)

    def update_recipe(self, query, body, user, family_id, dish_id: str = "") -> dict[str, Any]:
        return self.ctx.recipe.update(user, dish_id, body)

    def delete_recipe(self, query, body, user, family_id, dish_id: str = "") -> dict[str, Any]:
        """
        物理删除个人菜谱。

        被家庭菜单引用过的菜谱不允许删除（会破坏历史菜单），
        这类情况应改用 /archive 下架。
        """
        return self.ctx.recipe.delete(user, dish_id)

    def archive_recipe(self, query, body, user, family_id, dish_id: str = "") -> dict[str, Any]:
        return self.ctx.recipe.archive(user, dish_id)

    def restore_recipe(self, query, body, user, family_id, dish_id: str = "") -> dict[str, Any]:
        return self.ctx.recipe.restore(user, dish_id)

    def submit_recipe(self, query, body, user, family_id, dish_id: str = "") -> dict[str, Any]:
        return self.ctx.recipe.submit_review(user, dish_id)

    def withdraw_recipe(self, query, body, user, family_id, dish_id: str = "") -> dict[str, Any]:
        return self.ctx.recipe.withdraw_review(user, dish_id)

    def list_pending_recipes(self, query, body, user, family_id) -> dict[str, Any]:
        """待审核列表：非审核员由服务层抛 RecipeForbidden → 403。"""
        return self.ctx.recipe.list_pending(user)

    def review_recipe(self, query, body, user, family_id, dish_id: str = "") -> dict[str, Any]:
        """审核：body = {approve: bool, note: str}。"""
        approve = body.get("approve")
        if not isinstance(approve, bool):
            raise ApiError(400, "缺少参数：approve（布尔值）")
        note = body.get("note") or ""
        return self.ctx.recipe.review(user, dish_id, approve, note)

    def get_menu(self, query, body, user, family_id) -> dict[str, Any]:
        week_key = (query.get("week") or [None])[0]
        # 菜单按家庭隔离：同家庭成员看到同一份
        return self.ctx.order.get_week(family_id, week_key)

    def add_item(self, query, body, user, family_id) -> dict[str, Any]:
        dish_id = body.get("dishId")
        day = body.get("day")
        meal = body.get("meal")
        if not dish_id or not day or not meal:
            raise ApiError(400, "缺少参数：dishId / day / meal")
        qty = body.get("qty", 1)
        return self.ctx.order.add_item(family_id, dish_id, day, meal, qty)

    def set_quantity(self, query, body, user, family_id) -> dict[str, Any]:
        dish_id = body.get("dishId")
        day = body.get("day")
        meal = body.get("meal")
        if not dish_id or not day or not meal or "qty" not in body:
            raise ApiError(400, "缺少参数：dishId / day / meal / qty")
        return self.ctx.order.set_quantity(
            family_id, dish_id, day, meal, body["qty"]
        )

    def remove_item(self, query, body, user, family_id) -> dict[str, Any]:
        dish_id = body.get("dishId") or (query.get("dishId") or [None])[0]
        day = body.get("day") or (query.get("day") or [None])[0]
        meal = body.get("meal") or (query.get("meal") or [None])[0]
        if not dish_id or not day or not meal:
            raise ApiError(400, "缺少参数：dishId / day / meal")
        return self.ctx.order.remove_item(family_id, dish_id, day, meal)

    def generate_week(self, query, body, user, family_id) -> dict[str, Any]:
        return self.ctx.order.generate_week(family_id)

    def clear_week(self, query, body, user, family_id) -> dict[str, Any]:
        return self.ctx.order.clear_week(family_id)

    def get_nutrition(self, query, body, user, family_id) -> dict[str, Any]:
        return self.ctx.order.get_nutrition(family_id)

    def list_favorites(self, query, body, user, family_id) -> dict[str, Any]:
        return self.ctx.favorite.list(user.get("id", ""))

    def add_favorite(self, query, body, user, family_id) -> dict[str, Any]:
        dish_id = body.get("dishId")
        if not dish_id:
            raise ApiError(400, "缺少参数：dishId")
        return self.ctx.favorite.add(user.get("id", ""), dish_id)

    def remove_favorite(self, query, body, user, family_id, dish_id: str) -> dict[str, Any]:
        return self.ctx.favorite.remove(user.get("id", ""), dish_id)

    def toggle_favorite(self, query, body, user, family_id, dish_id: str) -> dict[str, Any]:
        return self.ctx.favorite.toggle(user.get("id", ""), dish_id)

    # ── 静态资源 ────────────────────────────────────────────────

    def _serve_static(self, path: str) -> None:
        static_dir = self.ctx.static_dir.resolve()
        rel = unquote(path).lstrip("/") or "index.html"
        target = (static_dir / rel).resolve()

        # 目录穿越防护：解析后的路径必须仍在静态根内
        if not str(target).startswith(str(static_dir)):
            self._send_text(403, "Forbidden")
            return

        if target.is_dir():
            target = target / "index.html"

        if not target.exists() or not target.is_file():
            # 前端是 hash 路由，未知路径回落到首页
            index = static_dir / "index.html"
            if index.exists():
                target = index
            else:
                self._send_text(404, "Not Found")
                return

        content_type, _ = mimetypes.guess_type(str(target))
        if content_type is None:
            content_type = "application/octet-stream"
        if content_type.startswith("text/") or content_type in (
            "application/javascript",
            "application/json",
        ):
            content_type += "; charset=utf-8"

        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    # ── 工具 ────────────────────────────────────────────────────

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ApiError(400, "请求体不是合法的 JSON")
        if not isinstance(parsed, dict):
            raise ApiError(400, "请求体必须是 JSON 对象")
        return parsed

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, status: int, message: str) -> None:
        data = message.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PATCH,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt: str, *args: Any) -> None:
        if not self.quiet:
            super().log_message(fmt, *args)


def create_server(host: str, port: int, ctx: AppContext, quiet: bool = False):
    """创建并返回 HTTP 服务器实例（未启动）。"""
    handler_cls = type("BoundRequestHandler", (RequestHandler,), {"ctx": ctx, "quiet": quiet})
    server = ThreadingHTTPServer((host, port), handler_cls)
    server.daemon_threads = True
    return server
