"""Rutas de comercio (carrito y tienda) para la capa de infraestructura."""

from functools import partial

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infraestructura.rutas.base import templates, LoggingRoute, logger
from src.infraestructura.tenant import resolutor_tenant
from src.infraestructura.datos import (
    cargar_site,
    cargar_carrito_defecto,
    cargar_tarifas,
)
from src.comercio.adaptadores.repositorios.cookie import RepositorioCarritoCookie
from src.comercio.aplicacion.casos_uso.carrito import (
    CasoUsoActualizarCarrito,
    CasoUsoAgregarAlCarrito,
)
from src.precios.adaptadores.servicios.cotizador import CotizadorServicio

router = APIRouter(route_class=LoggingRoute)


def obtener_catalogo_productos(tenant: str) -> list[dict]:
    """Devuelve el catálogo del tenant o una lista vacía si hay error."""
    try:
        return cargar_carrito_defecto(tenant)
    except Exception as err:
        logger.error(f"Error obteniendo catálogo para tenant '{tenant}': {err}", exc_info=True)
        return []


def obtener_tarifas(tenant: str) -> dict:
    """Devuelve las tarifas del tenant o un diccionario vacío si hay error."""
    try:
        return cargar_tarifas(tenant)
    except Exception as err:
        logger.error(f"Error obteniendo tarifas para tenant '{tenant}': {err}", exc_info=True)
        return {}


@router.get("/tienda/", response_class=HTMLResponse)
async def ver_tienda(
    request: Request,
    tenant: str = Depends(resolutor_tenant),
):
    sitio = cargar_site(tenant)
    catalogo = obtener_catalogo_productos(tenant)
    return templates.TemplateResponse(
        request=request,
        name="pages/tienda.html",
        context={"site": sitio, "productos": catalogo},
    )


@router.post("/carrito/agregar")
async def agregar_al_carrito(
    request: Request,
    tenant: str = Depends(resolutor_tenant),
    id_articulo: int = Form(...),
    cantidad: int = Form(...),
):
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_defecto_yaml=partial(obtener_catalogo_productos, tenant),
        registrar_error=logger.error,
    )

    caso_uso = CasoUsoAgregarAlCarrito(
        repositorio=repositorio,
        registrar_error=logger.error,
    )

    try:
        catalogo = obtener_catalogo_productos(tenant)
        caso_uso.ejecutar(id_articulo, cantidad, catalogo)
        logger.info(
            f"Tenant '{tenant}' | Artículo {id_articulo} agregado al carrito con cantidad {cantidad}"
        )
    except ValueError as err:
        logger.error(f"Error al agregar artículo {id_articulo} al carrito: {err}")
        return RedirectResponse(url="/tienda/?error=cantidad_invalida", status_code=303)

    respuesta = RedirectResponse(url="/carrito/", status_code=303)
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600 * 24 * 30,
            path="/",
        )
    return respuesta


@router.get("/carrito/", response_class=HTMLResponse)
async def ver_carrito(
    request: Request,
    tenant: str = Depends(resolutor_tenant),
):
    sitio = cargar_site(tenant)
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        cargar_defecto_yaml=partial(obtener_catalogo_productos, tenant),
        registrar_error=logger.error,
    )
    carrito = repositorio.obtener_carrito()

    cotizador = CotizadorServicio(
        cargar_tarifas_yaml=partial(obtener_tarifas, tenant),
        registrar_error=logger.error,
    )

    precio_total = 0.0
    for articulo in carrito.articulos:
        try:
            precio_total += cotizador.calcular_precio_estimado(articulo.id, articulo.cantidad)
        except Exception as err:
            logger.warning(f"No se pudo cotizar artículo {articulo.id}: {err}")

    if precio_total > 0:
        precio_estimado_formateado = f"$ {precio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        precio_estimado_formateado = "A cotizar"

    total_bolsas_formateado = f"{carrito.total_bolsas:,} unidades".replace(",", ".")

    if "cart" in sitio and "summary" in sitio["cart"]:
        sitio["cart"]["summary"]["estimated_cost_value"] = precio_estimado_formateado

    return templates.TemplateResponse(
        request=request,
        name="pages/carrito.html",
        context={
            "site": sitio,
            "cart_items": carrito.articulos,
            "total_bags_formatted": total_bolsas_formateado,
        },
    )


@router.post("/carrito/actualizar")
async def actualizar_carrito(
    request: Request,
    tenant: str = Depends(resolutor_tenant),
):
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
        cargar_defecto_yaml=partial(obtener_catalogo_productos, tenant),
        registrar_error=logger.error,
    )

    caso_uso = CasoUsoActualizarCarrito(
        repositorio=repositorio,
        registrar_error=logger.error,
    )
    caso_uso.ejecutar(actualizaciones)

    respuesta = RedirectResponse(url="/carrito/", status_code=303)
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600 * 24 * 30,
            path="/",
        )
    return respuesta
