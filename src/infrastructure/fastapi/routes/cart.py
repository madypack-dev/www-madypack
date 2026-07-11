from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infrastructure.fastapi.routes.base import templates, logger
from src.infrastructure.pyyaml.loaders import cargar_site
from src.domain.commerce.cart_repository import IRepositorioCarrito
from src.domain.commerce.catalog_repository import ICatalogRepository
from src.adapters.gateways.commerce_cookie_repository import RepositorioCarritoCookie
from src.application.commerce.cart_use_cases import (
    CasoUsoActualizarCarrito,
    CasoUsoAgregarAlCarrito,
    CasoUsoEliminarDelCarrito,
    CasoUsoObtenerResumenCarrito,
)
from src.adapters.gateways.pricing_service import CotizadorServicio
from src.adapters.presenters.commerce_presentation_helper import formatear_precio, formatear_unidades
from src.infrastructure.fastapi.dependencies import (
    get_repositorio_carrito,
    get_repositorio_catalogo,
    get_cotizador,
    get_caso_uso_agregar_carrito,
    get_caso_uso_eliminar_carrito,
    get_caso_uso_actualizar_carrito,
    get_caso_uso_obtener_resumen_carrito,
)


router = APIRouter()

@router.get("/tienda/", response_class=RedirectResponse, include_in_schema=False)
@router.get("/tienda", response_class=RedirectResponse, include_in_schema=False)
async def redirigir_tienda():
    return RedirectResponse(url="/productos/", status_code=301)


@router.get("/productos/", response_class=HTMLResponse)
async def ver_tienda(
    request: Request,
    q: str | None = None,
    repositorio_catalogo: ICatalogRepository = Depends(get_repositorio_catalogo),
):
    sitio = cargar_site()
    query_filtrada = q.strip() if q else ""
    productos = repositorio_catalogo.buscar(query_filtrada)

    return templates.TemplateResponse(
        request=request,
        name="pages/tienda.html",
        context={"site": sitio, "productos": productos, "q": query_filtrada},
    )


@router.get("/productos/{producto_slug}/", response_class=HTMLResponse)
async def ver_producto(
    request: Request,
    producto_slug: str,
    repositorio_catalogo: ICatalogRepository = Depends(get_repositorio_catalogo),
):
    sitio = cargar_site()
    producto_encontrado = repositorio_catalogo.obtener_por_slug(producto_slug)

    if producto_encontrado is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Obtener hasta 3 productos relacionados
    productos = repositorio_catalogo.obtener_todos()
    relacionados = [p for p in productos if p.id != producto_encontrado.id][:3]

    import json
    variaciones_list = [
        {
            "id": v.id,
            "sku": v.sku,
            "atributos": v.atributos,
            "imagen": v.imagen,
            "cantidad_por_defecto": v.cantidad_por_defecto
        }
        for v in producto_encontrado.variaciones
    ]

    return templates.TemplateResponse(
        request=request,
        name="pages/producto.html",
        context={
            "site": sitio,
            "producto": producto_encontrado,
            "relacionados": relacionados,
            "variaciones_json": json.dumps(variaciones_list),
        },
    )


@router.post("/cart/agregar")
async def agregar_al_carrito(
    request: Request,
    id_articulo: int = Form(...),
    cantidad: int = Form(...),
    repositorio: IRepositorioCarrito = Depends(get_repositorio_carrito),
    caso_uso: CasoUsoAgregarAlCarrito = Depends(get_caso_uso_agregar_carrito),
):
    try:
        caso_uso.ejecutar(id_articulo, cantidad)
        logger.info(
            f"Artículo {id_articulo} agregado al carrito con cantidad {cantidad}"
        )
    except ValueError as err:
        logger.error(f"Error al agregar artículo {id_articulo} al carrito: {err}")
        return RedirectResponse(url="/productos/?error=cantidad_invalida", status_code=303)

    respuesta = RedirectResponse(url="/cart/", status_code=303)
    if isinstance(repositorio, RepositorioCarritoCookie) and repositorio.carrito_serializado:
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
    repositorio: IRepositorioCarrito = Depends(get_repositorio_carrito),
    caso_uso: CasoUsoEliminarDelCarrito = Depends(get_caso_uso_eliminar_carrito),
):
    try:
        caso_uso.ejecutar(id_articulo)
        logger.info(f"Artículo {id_articulo} eliminado del carrito")
    except ValueError as err:
        logger.error(f"Error al eliminar artículo {id_articulo} del carrito: {err}")

    respuesta = RedirectResponse(url="/cart/", status_code=303)
    if isinstance(repositorio, RepositorioCarritoCookie) and repositorio.carrito_serializado:
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
    repositorio: IRepositorioCarrito = Depends(get_repositorio_carrito),
    cotizador: CotizadorServicio = Depends(get_cotizador),
    caso_uso: CasoUsoObtenerResumenCarrito = Depends(get_caso_uso_obtener_resumen_carrito),
):
    sitio = cargar_site()
    carrito = repositorio.obtener_carrito()
    resumen = caso_uso.ejecutar(carrito, cotizador)

    return templates.TemplateResponse(
        request=request,
        name="pages/carrito.html",
        context={
            "site": sitio,
            "cart_items": resumen.articulos,
            "total_bags_formatted": formatear_unidades(resumen.total_bolsas),
            "estimated_cost_formatted": formatear_precio(resumen.precio_total),
        },
    )


@router.post("/cart/actualizar")
async def actualizar_carrito(
    request: Request,
    repositorio: IRepositorioCarrito = Depends(get_repositorio_carrito),
    caso_uso: CasoUsoActualizarCarrito = Depends(get_caso_uso_actualizar_carrito),
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

    caso_uso.ejecutar(actualizaciones)

    respuesta = RedirectResponse(url="/cart/", status_code=303)
    if isinstance(repositorio, RepositorioCarritoCookie) and repositorio.carrito_serializado:
        respuesta.set_cookie(
            key="articulos_carrito",
            value=repositorio.carrito_serializado,
            max_age=3600 * 24 * 30,
            path="/",
        )
    return respuesta
