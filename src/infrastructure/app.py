from pathlib import Path
from typing import Any, cast

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="FastAPI con Jinja2")

# Montar los archivos estáticos (CSS, JS, Imágenes)
# 'directory="static"' busca la carpeta en la raíz desde donde se ejecuta el script
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar el motor de plantillas Jinja2
templates = Jinja2Templates(directory="templates")

# Cargar la configuración del sitio desde data/*.yml
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_SITE_YAML = _DATA_DIR / "site.yml"


def _load_site_data() -> dict[str, Any]:
    if not _SITE_YAML.exists():
        return {}
    with _SITE_YAML.open("r", encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f) or {})


SITE_DATA: dict[str, Any] = _load_site_data()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Pasamos el 'request' obligatoriamente y el contenido del YAML al contexto de Jinja2
    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={"site": SITE_DATA},
    )
