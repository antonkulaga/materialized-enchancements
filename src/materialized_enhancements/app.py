from __future__ import annotations

import base64
import binascii
import json
import logging
import re

import reflex as rx
from reflex.app import default_frontend_exception_handler
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

import materialized_enhancements.pages.index  # noqa: F401 — registers pages via @rx.page
from materialized_enhancements.env import (
    GENERATED_PUBLIC_DIR,
    GENERATED_URL_PREFIX,
    UMAMI_DOMAINS,
    UMAMI_HOST_URL,
    UMAMI_SCRIPT_URL,
    UMAMI_WEBSITE_ID,
    ensure_generated_public_dirs,
)

logger = logging.getLogger(__name__)


ensure_generated_public_dirs()
_generated_static = StaticFiles(directory=GENERATED_PUBLIC_DIR, check_dir=False)
DESKTOP_VIEWPORT_WIDTH_PX = 1440
_SUPPRESSED_3DMOL_FRONTEND_ERROR_MARKERS = (
    "OffscreenCanvas.transferToImageBitmap",
    "3dmol",
    "spinInterval",
)
_logged_suppressed_3dmol_frontend_error = False

_head_components: list[rx.Component] = [
    rx.el.meta(name="viewport", content=f"width={DESKTOP_VIEWPORT_WIDTH_PX}"),
]

if UMAMI_SCRIPT_URL and UMAMI_WEBSITE_ID:
    _umami_attrs: dict[str, str] = {"data-website-id": UMAMI_WEBSITE_ID}
    if UMAMI_DOMAINS:
        _umami_attrs["data-domains"] = UMAMI_DOMAINS
    if UMAMI_HOST_URL:
        _umami_attrs["data-host-url"] = UMAMI_HOST_URL
    _head_components.append(
        rx.script(src=UMAMI_SCRIPT_URL, custom_attrs=_umami_attrs)
    )


def _handle_frontend_exception(exception: Exception) -> None:
    """Suppress noisy stale-client 3Dmol canvas errors; keep normal Reflex logging."""
    global _logged_suppressed_3dmol_frontend_error

    message = str(exception).lower()
    if all(marker.lower() in message for marker in _SUPPRESSED_3DMOL_FRONTEND_ERROR_MARKERS):
        if not _logged_suppressed_3dmol_frontend_error:
            logger.warning("Suppressing repeated stale-client 3Dmol OffscreenCanvas frontend errors")
            _logged_suppressed_3dmol_frontend_error = True
        return

    default_frontend_exception_handler(exception)


_SLUG_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,200}$")
_MAX_UPLOAD_BYTES = 40 * 1024 * 1024  # 40 MB


async def _handle_upload_report_assets(scope: Scope, receive: Receive, send: Send) -> None:
    """HTTP POST endpoint that receives report PNG+PDF via fetch(), bypassing WebSocket size limits."""
    request = Request(scope, receive, send)
    if request.method != "POST":
        resp = JSONResponse({"error": "Method not allowed"}, status_code=405)
        await resp(scope, receive, send)
        return
    try:
        body = await request.body()
        if len(body) > _MAX_UPLOAD_BYTES:
            resp = JSONResponse({"error": "Payload too large"}, status_code=413)
            await resp(scope, receive, send)
            return
        data = json.loads(body)
        slug = str(data.get("slug", "")).strip()
        if not slug or not _SLUG_RE.match(slug):
            resp = JSONResponse({"error": "Invalid slug"}, status_code=400)
            await resp(scope, receive, send)
            return
        png_b64 = str(data.get("png_base64", "")).strip()
        pdf_b64 = str(data.get("pdf_base64", "")).strip()
        if not png_b64 or not pdf_b64:
            resp = JSONResponse({"error": "Missing png_base64 or pdf_base64"}, status_code=400)
            await resp(scope, receive, send)
            return
        out_dir = GENERATED_PUBLIC_DIR / "reports" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        png_bytes = base64.b64decode(png_b64, validate=True)
        pdf_bytes = base64.b64decode(pdf_b64, validate=True)
        (out_dir / "report.webp").write_bytes(png_bytes)
        (out_dir / "report.pdf").write_bytes(pdf_bytes)
        portrait_b64 = str(data.get("portrait_base64", "")).strip()
        if portrait_b64:
            try:
                (out_dir / "portrait.webp").write_bytes(base64.b64decode(portrait_b64, validate=True))
            except (binascii.Error, ValueError):
                pass
        logger.info("Report assets uploaded for slug=%s (png=%d, pdf=%d bytes)", slug, len(png_bytes), len(pdf_bytes))
        resp = JSONResponse({"status": "ok", "slug": slug})
        await resp(scope, receive, send)
    except (json.JSONDecodeError, binascii.Error, ValueError) as exc:
        resp = JSONResponse({"error": str(exc)}, status_code=400)
        await resp(scope, receive, send)
    except OSError as exc:
        logger.exception("Report asset upload I/O error")
        resp = JSONResponse({"error": f"Server I/O error: {exc}"}, status_code=500)
        await resp(scope, receive, send)


def normalize_reflex_event_websocket_path(app: ASGIApp) -> ASGIApp:
    """Route generated files, upload endpoint, and keep WebSocket scopes away from the static catch-all."""

    async def wrapped_app(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = str(scope.get("path", ""))
            if path == "/_api/upload-report-assets":
                await _handle_upload_report_assets(scope, receive, send)
                return
            if path == GENERATED_URL_PREFIX or path.startswith(f"{GENERATED_URL_PREFIX}/"):
                generated_path = path.removeprefix(GENERATED_URL_PREFIX) or "/"
                static_scope = {
                    **scope,
                    "path": generated_path,
                    "root_path": f"{scope.get('root_path', '')}{GENERATED_URL_PREFIX}",
                }
                await _generated_static(static_scope, receive, send)
                return
        if scope["type"] == "websocket":
            path = str(scope.get("path", ""))
            if path == "/_event":
                scope = {**scope, "path": "/_event/", "raw_path": b"/_event/"}
            elif not path.startswith("/_event/"):
                await send({"type": "websocket.close", "code": 1000})
                return
        await app(scope, receive, send)

    return wrapped_app


app = rx.App(
    head_components=_head_components,
    frontend_exception_handler=_handle_frontend_exception,
    api_transformer=normalize_reflex_event_websocket_path,
)
