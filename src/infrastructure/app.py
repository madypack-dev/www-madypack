from datetime import date
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.infrastructure.routes.pages import router as pages_router
from src.infrastructure.routes.cart import router as cart_router

app = FastAPI(title="Madypack")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/robots.txt", response_class=FileResponse)
async def robots_txt():
    return FileResponse(Path(__file__).resolve().parents[2] / "static" / "robots.txt")


@app.get("/sitemap.xml")
async def sitemap_xml():
    today = date.today().isoformat()
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.madypack.com.ar/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/quienes-somos/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/cotizacion/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/contacto/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/terminos-y-condiciones/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>https://www.madypack.com.ar/politica-de-privacidad/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>
"""
    return Response(content=xml_content, media_type="application/xml")


app.include_router(pages_router)
app.include_router(cart_router)
