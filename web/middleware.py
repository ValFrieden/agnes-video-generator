"""web.middleware — HTTP 请求级中间件（v7.0）。

目前只承载一个中间件：``LangContextMiddleware``，把前端注入的
``X-Agnes-UI-Lang`` 头（或 ``Accept-Language`` 兜底）写入
``core.i18n_backend.current_lang`` ContextVar，供同请求生命周期内的
``HTTPException(detail=translate(...))`` 与短同步代码读取。

**异步 Pipeline 不走这里**：任务在后台协程里跑，请求上下文早已切走，
Pipeline 通过 ``BaseTaskState.ui_language``（任务创建时落盘）拿到语言。
"""
from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from core.i18n_backend import (
    UI_LANG_HEADER,
    current_lang,
    normalize_lang,
    parse_accept_language,
)

logger = logging.getLogger(__name__)

__all__ = ["LangContextMiddleware", "OriginGuardMiddleware", "extract_request_lang"]


def extract_request_lang(request: Request) -> str:
    """按优先级从请求里提取 UI 语言：自定义头 > ``Accept-Language`` > ``zh``。

    Args:
        request: Starlette/FastAPI 请求对象。

    Returns:
        归一化后的 2 字母语言代码，永远落在 ``SUPPORTED_UI_LANGS`` 内。
    """
    header_lang = request.headers.get(UI_LANG_HEADER)
    if header_lang:
        return normalize_lang(header_lang)
    return parse_accept_language(request.headers.get("accept-language"))


class LangContextMiddleware(BaseHTTPMiddleware):
    """把请求级 UI 语言写入 ContextVar，供同请求内的 ``translate()`` 读取。

    实现要点：
    - 使用 ``BaseHTTPMiddleware`` 而非纯 ASGI 中间件：本仓库已经在
      ``server.py`` 里以 ``add_middleware`` 形式挂 CORS，风格一致，
      且我们只需要在 dispatch 前后各做一次 ContextVar 读写；
    - ``finally`` 里 ``current_lang.reset(token)``：避免同一个协程池复用
      时残留上一个请求的语言（ContextVar 在 asyncio Task 边界自动隔离，
      但 Starlette 的 BaseHTTPMiddleware 会为每个请求起独立 Task，
      保险起见仍显式 reset）；
    - 不抛异常：语言解析失败一律回退默认 ``zh``，绝不让 i18n 缺陷把
      正常业务请求打断。
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: D401
        lang = extract_request_lang(request)
        token = current_lang.set(lang)
        try:
            return await call_next(request)
        finally:
            current_lang.reset(token)


# ── Logikcheck Befund 5：跨站写请求防护 ─────────────────────────────────────
# 本服务默认无任何认证（本地工具定位），而 multipart POST / 无 body DELETE 属于
# CORS "simple request"——浏览器不发送预检，任意第三方网页都可以在用户打开本应用
# 时携带其 Cookie/网络位置直接提交（例如覆盖 /api/config 的 API Key、创建任务）。
# 浏览器对跨站请求必带 Origin 头（同站 POST 也会带），因此对**写方法**做
# Origin↔Host 一致性校验即可挡住跨站伪造，同时不影响 curl / 脚本调用（无 Origin）。
_UNSAFE_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})


def _allowed_hosts() -> list[str]:
    """读取 AGNES_ALLOWED_HOSTS（逗号分隔）。设置后所有请求的 Host 都必须在列表内。

    经 ``get_settings()`` 读取（.env 文件同样生效），settings 不可用时回退 os.environ。
    """
    try:
        from core.config import get_settings
        raw = (get_settings().agnes_allowed_hosts or "").strip()
    except Exception:
        raw = (os.environ.get("AGNES_ALLOWED_HOSTS") or "").strip()
    return [h.strip().lower() for h in raw.split(",") if h.strip()]


class OriginGuardMiddleware(BaseHTTPMiddleware):
    """写方法 Origin 一致性校验 + 可选 Host 白名单（DNS rebinding 缓解）。

    - Origin 头存在且其 host:port 与请求 Host 不一致 → 403（跨站伪造写请求）。
      反向代理场景优先比对 ``X-Forwarded-Host``。
    - ``AGNES_ALLOWED_HOSTS`` 非空时，Host 不在白名单 → 403（缓解 DNS rebinding）。
      默认空 = 不限制，公网域名部署不受影响。
    - 无 Origin 的请求（curl / 同源 GET / 老客户端）直接放行，保持 CLI 可用。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        allowed = _allowed_hosts()
        req_host = (
            request.headers.get("x-forwarded-host")
            or request.headers.get("host")
            or ""
        ).lower()
        if allowed and req_host and req_host not in allowed:
            return JSONResponse(
                {"detail": "Host not allowed"}, status_code=403,
            )

        if request.method in _UNSAFE_METHODS:
            origin = request.headers.get("origin")
            if origin is not None:
                origin_host = urlparse(origin).netloc.lower()
                if not req_host or origin_host != req_host:
                    return JSONResponse(
                        {"detail": "Cross-origin request rejected"}, status_code=403,
                    )
        return await call_next(request)
