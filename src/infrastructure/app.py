from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI(title="FastAPI con Jinja2")

# Montar los archivos estáticos (CSS, JS, Imágenes)
# 'directory="static"' busca la carpeta en la raíz desde donde se ejecuta el script
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar el motor de plantillas Jinja2
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Pasamos el 'request' obligatoriamente y variables opcionales al contexto de Jinja2
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Inicio", "message": "¡Servidor FastAPI funcionando con Jinja2!"}
    )
