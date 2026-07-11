"""Rutas de comercio (carrito y tienda) para la capa de infraestructura."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infrastructure.rutas.base import templates, logger
from src.infrastructure.datos.cargadores import cargar_site
from src.infrastructure.datos.proveedores import (
    obtener_productos_tienda,
    obtener_tarifas,
)
from src.adapters.comercio.repositorios.cookie import RepositorioCarritoCookie
from src.application.comercio.casos_uso.carrito import (
    CasoUsoActualizarCarrito,
    CasoUsoAgregarAlCarrito,
    CasoUsoEliminarDelCarrito,
    CasoUsoObtenerResumenCarrito,
)
from src.adapters.precios.servicios.cotizador import CotizadorServicio

router = APIRouter()

@router.get("/tienda/", response_class=RedirectResponse, include_in_schema=False)
@router.get("/tienda", response_class=RedirectResponse, include_in_schema=False)
async def redirigir_tienda():
    return RedirectResponse(url="/productos/", status_code=301)


@router.get("/productos/", response_class=HTMLResponse)
async def ver_tienda(
    request: Request,
    q: str | None = None,
):
    sitio = cargar_site()
    productos = obtener_productos_tienda()

    query_filtrada = q.strip() if q else ""
    if query_filtrada:
        query_lower = query_filtrada.lower()
        productos = [
            p for p in productos
            if query_lower in p.nombre.lower() or query_lower in p.descripcion.lower()
        ]

    return templates.TemplateResponse(
        request=request,
        name="pages/tienda.html",
        context={"site": sitio, "productos": productos, "q": query_filtrada},
    )


@router.get("/productos/{producto_slug}/", response_class=HTMLResponse)
async def ver_producto(
    request: Request,
    producto_slug: str,
):
    sitio = cargar_site()
    productos = obtener_productos_tienda()

    # Buscar el producto por su slug
    producto_encontrado = None
    for p in productos:
        if p.url_slug == producto_slug:
            producto_encontrado = p
            break

    if producto_encontrado is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Obtener hasta 3 productos relacionados
    relacionados = [p for p in productos if p.id != producto_encontrado.id][:3]

    return templates.TemplateResponse(
        request=request,
        name="pages/producto.html",
        context={
            "site": sitio,
            "producto": producto_encontrado,
            "relacionados": relacionados,
        },
    )


@router.post("/cart/agregar")
async def agregar_al_carrito(
    request: Request,
    id_articulo: int = Form(...),
    cantidad: int = Form(...),
):
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        registrar_error=logger.error,
    )

    caso_uso = CasoUsoAgregarAlCarrito(
        repositorio=repositorio,
        registrar_error=logger.error,
    )

    try:
        productos = obtener_productos_tienda()
        caso_uso.ejecutar(id_articulo, cantidad, productos)
        logger.info(
            f"Artículo {id_articulo} agregado al carrito con cantidad {cantidad}"
        )
    except ValueError as err:
        logger.error(f"Error al agregar artículo {id_articulo} al carrito: {err}")
        return RedirectResponse(url="/productos/?error=cantidad_invalida", status_code=303)

    respuesta = RedirectResponse(url="/cart/", status_code=303)
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600 * 24 * 30,
            path="/",
        )
    return respuesta


@router.post("/cart/eliminar")
async def eliminar_del_carrito(
    request: Request,
    id_articulo: int = Form(...),
):
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        registrar_error=logger.error,
    )

    caso_uso = CasoUsoEliminarDelCarrito(
        repositorio=repositorio,
        registrar_error=logger.error,
    )

    try:
        caso_uso.ejecutar(id_articulo)
        logger.info(f"Artículo {id_articulo} eliminado del carrito")
    except ValueError as err:
        logger.error(f"Error al eliminar artículo {id_articulo} del carrito: {err}")

    respuesta = RedirectResponse(url="/cart/", status_code=303)
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600 * 24 * 30,
            path="/",
        )
    else:
        respuesta.delete_cookie(key="articulos_carrito", path="/")
    return respuesta


@router.get("/cart/", response_class=HTMLResponse)
async def ver_carrito(
    request: Request,
):
    sitio = cargar_site()
    repositorio = RepositorioCarritoCookie(
        cookies=request.cookies,
        registrar_error=logger.error,
    )
    carrito = repositorio.obtener_carrito()

    cotizador = CotizadorServicio(
        cargar_tarifas_yaml=obtener_tarifas,
        registrar_error=logger.error,
    )

    caso_uso = CasoUsoObtenerResumenCarrito(registrar_error=logger.warning)
    resumen = caso_uso.ejecutar(carrito, cotizador)

    return templates.TemplateResponse(
        request=request,
        name="pages/carrito.html",
        context={
            "site": sitio,
            "cart_items": resumen.articulos,
            "total_bags_formatted": resumen.total_bolsas_formateado,
            "estimated_cost_formatted": resumen.precio_estimado_formateado,
        },
    )


@router.post("/cart/actualizar")
async def actualizar_carrito(
    request: Request,
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
        registrar_error=logger.error,
    )

    caso_uso = CasoUsoActualizarCarrito(
        repositorio=repositorio,
        registrar_error=logger.error,
    )
    caso_uso.ejecutar(actualizaciones)

    respuesta = RedirectResponse(url="/cart/", status_code=303)
    if repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600 * 24 * 30,
            path="/",
        )
    return respuesta
