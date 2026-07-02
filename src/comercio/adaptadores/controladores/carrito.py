from pathlib import Path
import yaml  # type: ignore
import json
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infraestructura.rutas.base import templates, load_site, LoggingRoute, logger
from src.comercio.adaptadores.repositorios.cookie import RepositorioCarritoCookie
from src.comercio.aplicacion.casos_uso.carrito import CasoUsoActualizarCarrito, CasoUsoAgregarAlCarrito
from src.precios.adaptadores.servicios.cotizador import CotizadorServicio

router = APIRouter(route_class=LoggingRoute)

PATH_CARRITO_YAML = Path(__file__).resolve().parents[4] / "data" / "carrito_defecto.yml"
PATH_TARIFAS_YAML = Path(__file__).resolve().parents[4] / "data" / "tarifas.yml"


def obtener_catalogo_productos() -> list[dict]:
    if not PATH_CARRITO_YAML.exists():
        logger.error(f"No se encontró el catálogo YAML en: {PATH_CARRITO_YAML}")
        return []
    try:
        contenido = yaml.safe_load(PATH_CARRITO_YAML.read_text(encoding="utf-8"))
        return contenido.get("articulos", [])
    except Exception as err:
        logger.error(f"Error parseando catálogo de productos: {err}", exc_info=True)
        return []


def obtener_tarifas() -> dict:
    if not PATH_TARIFAS_YAML.exists():
        logger.error(f"No se encontró el archivo de tarifas en: {PATH_TARIFAS_YAML}")
        return {}
    try:
        return yaml.safe_load(PATH_TARIFAS_YAML.read_text(encoding="utf-8")) or {}
    except Exception as err:
        logger.error(f"Error parseando archivo de tarifas: {err}", exc_info=True)
        return {}


@router.get("/tienda/", response_class=HTMLResponse)
async def ver_tienda(request: Request, sitio: dict = Depends(load_site)):
    catalogo = obtener_catalogo_productos()
    return templates.TemplateResponse(
        request=request,
        name="pages/tienda.html",
        context={"site": sitio, "productos": catalogo}
    )


@router.post("/carrito/agregar")
async def agregar_al_carrito(
    request: Request,
    id_articulo: int = Form(...),
    cantidad: int = Form(...)
):
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_defecto_yaml=obtener_catalogo_productos,
        registrar_error=logger.error
    )
    
    caso_uso = CasoUsoAgregarAlCarrito(
        repositorio=repositorio,
        registrar_error=logger.error
    )
    
    try:
        catalogo = obtener_catalogo_productos()
        caso_uso.ejecutar(id_articulo, cantidad, catalogo)
        logger.info(f"Artículo {id_articulo} agregado al carrito con cantidad {cantidad}")
    except ValueError as err:
        logger.error(f"Error al agregar artículo {id_articulo} al carrito: {err}")
        return RedirectResponse(url="/tienda/?error=cantidad_invalida", status_code=303)

    respuesta = RedirectResponse(url="/carrito/", status_code=303)
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600*24*30,
            path="/"
        )
    return respuesta


@router.get("/carrito/", response_class=HTMLResponse)
async def ver_carrito(request: Request, sitio: dict = Depends(load_site)):
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_defecto_yaml=obtener_catalogo_productos,
        registrar_error=logger.error
    )
    carrito = repositorio.obtener_carrito()
    
    # Calcular precio estimado usando el motor de precios
    cotizador = CotizadorServicio(
        cargar_tarifas_yaml=obtener_tarifas,
        registrar_error=logger.error
    )
    
    precio_total = 0.0
    for articulo in carrito.articulos:
        try:
            precio_total += cotizador.calcular_precio_estimado(articulo.id, articulo.cantidad)
        except Exception as err:
            logger.warning(f"No se pudo cotizar artículo {articulo.id}: {err}")
            
    # Formatear el precio total y la cantidad total de bolsas
    if precio_total > 0:
        precio_estimado_formateado = f"$ {precio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        precio_estimado_formateado = "A cotizar"
        
    total_bolsas_formateado = f"{carrito.total_bolsas:,} unidades".replace(",", ".")
    
    # Actualizar dinámicamente el valor en el contexto para el resumen
    if "cart" in sitio and "summary" in sitio["cart"]:
        sitio["cart"]["summary"]["estimated_cost_value"] = precio_estimado_formateado
        
    return templates.TemplateResponse(
        request=request,
        name="pages/carrito.html",
        context={
            "site": sitio,
            "cart_items": carrito.articulos,
            "total_bags_formatted": total_bolsas_formateado
        },
    )


@router.post("/carrito/actualizar")
async def actualizar_carrito(request: Request):
    datos_formulario = await request.form()
    
    actualizaciones = {}
    for clave, valor in datos_formulario.items():
        if clave.startswith("qty_") and isinstance(valor, str):
            try:
                id_articulo = int(clave.replace("qty_", ""))
                actualizaciones[id_articulo] = int(valor)
            except ValueError:
                continue

    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_defecto_yaml=obtener_catalogo_productos,
        registrar_error=logger.error
    )
    
    caso_uso = CasoUsoActualizarCarrito(
        repositorio=repositorio,
        registrar_error=logger.error
    )
    caso_uso.ejecutar(actualizaciones)
    
    respuesta = RedirectResponse(url="/carrito/", status_code=303)
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600*24*30,
            path="/"
        )
    return respuesta
