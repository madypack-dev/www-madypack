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
from src.domain.commerce.product import ProductoBien
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
    todos = repositorio_catalogo.buscar(query_filtrada)
    productos = [p for p in todos if isinstance(p, ProductoBien) and p.visible]

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

    if not isinstance(producto_encontrado, ProductoBien) or not producto_encontrado.visible:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Obtener hasta 3 productos relacionados (solo comercializables y visibles)
    productos = [
        p
        for p in repositorio_catalogo.obtener_todos()
        if isinstance(p, ProductoBien) and p.visible
    ]
    relacionados = [p for p in productos if p.id != producto_encontrado.id][:3]

    variaciones_json = "[]"
    atributos_posibles = {}
    variacion_inicial = None
    if not producto_encontrado.es_compuesto:
        import json
        visible_variaciones = [v for v in producto_encontrado.variaciones if v.visible]
        if not visible_variaciones:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        variacion_inicial = visible_variaciones[0]
        variaciones_list = [
            {
                "id": v.id,
                "sku": v.sku,
                "atributos": v.atributos,
                "imagen": v.imagen,
                "cantidad_por_defecto": v.cantidad_por_defecto,
            }
            for v in visible_variaciones
        ]
        variaciones_json = json.dumps(variaciones_list)

        # Calcular atributos posibles restringidos a las variaciones visibles
        atributos_posibles = _atributos_desde_variaciones(
            producto_encontrado.atributos_posibles, visible_variaciones
        )

    return templates.TemplateResponse(
        request=request,
        name="pages/producto.html",
        context={
            "site": sitio,
            "producto": producto_encontrado,
            "relacionados": relacionados,
            "variaciones_json": variaciones_json,
            "atributos_posibles": atributos_posibles,
            "variacion_inicial": variacion_inicial,
        },
    )


def _atributos_desde_variaciones(
    atributos_posibles: dict[str, list[str]],
    variaciones: list,
) -> dict[str, list[str]]:
    """Filtra los atributos posibles dejando solo los valores presentes en las variaciones."""
    valores_usados: dict[str, set[str]] = {}
    for variacion in variaciones:
        for attr, valor in variacion.atributos.items():
            valores_usados.setdefault(attr, set()).add(valor)

    return {
        attr: [valor for valor in atributos_posibles.get(attr, []) if valor in valores_usados.get(attr, set())]
        for attr in atributos_posibles
    }


@router.post("/cart/agregar")
async def agregar_al_carrito(
    request: Request,
    producto_id: int = Form(...),
    cantidad: int = Form(...),
    variacion_id: int | None = Form(None),
    repositorio: IRepositorioCarrito = Depends(get_repositorio_carrito),
    caso_uso: CasoUsoAgregarAlCarrito = Depends(get_caso_uso_agregar_carrito),
):
    try:
        caso_uso.ejecutar(producto_id, variacion_id, cantidad)
        logger.info(
            f"Producto {producto_id} agregado al carrito con cantidad {cantidad}"
        )
    except ValueError as err:
        logger.error(f"Error al agregar producto {producto_id} al carrito: {err}")
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
