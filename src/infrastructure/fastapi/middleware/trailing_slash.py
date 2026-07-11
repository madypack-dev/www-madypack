"""Middleware para normalizar URLs con trailing slash."""

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method not in {"GET", "HEAD"}:
            return await call_next(request)

        exclusiones = {"/health", "/robots.txt", "/sitemap.xml"}
        es_estatico = path.startswith("/static/")
        tiene_extension = "." in path.split("/")[-1]

        if (
            path != "/"
            and not path.endswith("/")
            and not es_estatico
            and not tiene_extension
            and path not in exclusiones
        ):
            query = f"?{request.url.query}" if request.url.query else ""
            return RedirectResponse(url=f"{path}/{query}", status_code=301)

        return await call_next(request)
