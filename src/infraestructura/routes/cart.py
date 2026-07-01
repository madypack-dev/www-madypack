import json
from typing import Any
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infraestructura.routes.base import templates, load_site, LoggingRoute

router = APIRouter(route_class=LoggingRoute)

DEFAULT_CART = [
    {
        "id": 1,
        "name": "Bolsas de Papel Kraft Personalizadas",
        "description": "Impresión Flexográfica | Manijas planas",
        "quantity": 1000,
        "image": "bolsas-personalizadas.svg"
    },
    {
        "id": 2,
        "name": "Bolsas Kraft con Manija Cordón",
        "description": "Lisas estándar | 26x12x35 cm",
        "quantity": 2500,
        "image": "bolsas-con-m.svg"
    }
]


def get_cart_items(request: Request) -> list[dict[str, Any]]:
    cart_cookie = request.cookies.get("cart_items")
    if cart_cookie:
        try:
            return json.loads(cart_cookie)
        except Exception:
            pass
    return DEFAULT_CART


@router.get("/cart/", response_class=HTMLResponse)
async def read_cart(
    request: Request,
    site: dict[str, Any] = Depends(load_site),
    cart_items: list[dict[str, Any]] = Depends(get_cart_items)
):
    cart_cookie = request.cookies.get("cart_items")
    total_bags = sum(item.get("quantity", 0) for item in cart_items)
    total_bags_formatted = f"{total_bags:,} unidades".replace(",", ".")
    
    response = templates.TemplateResponse(
        request=request,
        name="pages/cart.html",
        context={
            "site": site,
            "cart_items": cart_items,
            "total_bags_formatted": total_bags_formatted
        },
    )
    
    if not cart_cookie:
        response.set_cookie(
            key="cart_items",
            value=json.dumps(DEFAULT_CART),
            max_age=3600*24*30,
            path="/"
        )
        
    return response


@router.post("/cart/update")
async def update_cart(
    request: Request,
    cart_items: list[dict[str, Any]] = Depends(get_cart_items)
):
    form_data = await request.form()
    
    for item in cart_items:
        field_name = f"qty_{item['id']}"
        if field_name in form_data:
            val = form_data[field_name]
            if isinstance(val, str):
                try:
                    new_qty = int(val)
                    if new_qty > 0:
                        item["quantity"] = new_qty
                except ValueError:
                    pass
                
    response = RedirectResponse(url="/cart/", status_code=303)
    response.set_cookie(
        key="cart_items",
        value=json.dumps(cart_items),
        max_age=3600*24*30,
        path="/"
    )
    return response
