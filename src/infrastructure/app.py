from pathlib import Path
from typing import Any, cast

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Madypack")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

SITE_YAML = Path(__file__).resolve().parents[2] / "data" / "site.yml"


def load_site() -> dict[str, Any]:
    if not SITE_YAML.exists():
        return {}
    return cast(dict[str, Any], yaml.safe_load(SITE_YAML.read_text(encoding="utf-8")) or {})


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={"site": load_site()},
    )
