"""Rutas de SEO técnico: sitemap.xml y robots.txt."""

from fastapi import APIRouter, Depends, Response, Request
from src.domain.comercio.catalog_repository import ICatalogRepository
from src.infrastructure.fastapi.dependencies import get_repositorio_catalogo
from src.infrastructure.fastapi.routes.base import load_site
from src.infrastructure.pyyaml.models import SiteConfig

router = APIRouter(tags=["SEO"])

@router.get("/sitemap.xml", response_class=Response)

def sitemap_xml(
    request: Request,
    catalog_repo: ICatalogRepository = Depends(get_repositorio_catalogo),
    site: SiteConfig = Depends(load_site)
) -> Response:
    base_url = str(request.base_url).rstrip("/")
    
    # Rutas estáticas clave
    urls = [
        f"{base_url}/",
        f"{base_url}/productos/",
        f"{base_url}/quienes-somos/",
        f"{base_url}/cotizacion/",
        f"{base_url}/personalizar/",
        f"{base_url}/contacto/",
    ]
    
    # Obtener dinámicamente las URLs de los productos del catálogo
    try:
        productos = catalog_repo.obtener_todos()
        for prod in productos:
            urls.append(f"{base_url}/productos/{prod.slug}/")
    except Exception:
        pass

    urlset_xml = "".join([f"<url><loc>{url}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>" for url in urls])
    xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urlset_xml}\n</urlset>'
    
    return Response(content=xml_content, media_type="application/xml")

@router.get("/robots.txt", response_class=Response)
def robots_txt(request: Request) -> Response:
    base_url = str(request.base_url).rstrip("/")
    content = f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n"
    return Response(content=content, media_type="text/plain")
