from datetime import date
import time
import logging
from pathlib import Path
from typing import Callable, Any, cast
import yaml
from fastapi import Request, Response
from fastapi.routing import APIRoute
from fastapi.templating import Jinja2Templates

logger = logging.getLogger("madypack")
logging.basicConfig(level=logging.INFO)

templates = Jinja2Templates(directory="templates")
SITE_YAML = Path(__file__).resolve().parents[3] / "data" / "site.yml"


def load_site() -> dict[str, Any]:
    if not SITE_YAML.exists():
        return {}
    return cast(dict[str, Any], yaml.safe_load(SITE_YAML.read_text(encoding="utf-8")) or {})


class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()
            try:
                response: Response = await original_route_handler(request)
                duration = time.time() - start_time
                logger.info(
                    f"Method: {request.method} | Path: {request.url.path} | "
                    f"Status: {response.status_code} | Duration: {duration:.4f}s"
                )
                return response
            except Exception as exc:
                duration = time.time() - start_time
                logger.error(
                    f"EXCEPTION - Method: {request.method} | Path: {request.url.path} | "
                    f"Duration: {duration:.4f}s | Error: {str(exc)}",
                    exc_info=True
                )
                raise exc
                
        return custom_route_handler
