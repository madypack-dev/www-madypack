"""Adaptador que utiliza Pillow para procesar la imagen y generar el SVG de fotopolímero en blanco y negro."""

import base64
from io import BytesIO
from PIL import Image

from src.domain.personalizacion.customization import PersonalizacionBolsa
from src.domain.personalizacion.customization_ports import IGeneradorFotopolimeroSVG


class GeneradorFotopolimeroPillowAdapter(IGeneradorFotopolimeroSVG):
    """Adaptador de fotopolímero: convierte la imagen a blanco y negro estricto y embebe el trazado en un lienzo SVG."""

    def generar_svg_fotopolimero(self, personalizacion: PersonalizacionBolsa) -> str:
        esp = personalizacion.especificacion
        ancho_util, alto_util = personalizacion.calcular_area_util_impresion()

        # Lienzo en píxeles (escala 1 cm = 40 px para alta definición)
        px_por_cm = 40
        view_w = int(esp.ancho_cm * px_por_cm)
        view_h = int(esp.alto_cm * px_por_cm)

        b64_img = ""
        try:
            with Image.open(BytesIO(personalizacion.diseno.contenido_bytes)) as img:
                # Convertir a escala de grises y binarizar (threshold a 128)
                img_gray = img.convert("L")
                # Threshold para binarización B&N estricto
                threshold = 128
                img_bw = img_gray.point(lambda p: 255 if p > threshold else 0, mode="1")

                buffer = BytesIO()
                img_bw.save(buffer, format="PNG")
                b64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception:
            # Si no es una imagen válida o es un formato vector pasante, se embebe directamente
            b64_img = base64.b64encode(personalizacion.diseno.contenido_bytes).decode("utf-8")

        # Coordenadas centradas para la estampa
        estampa_w = int(ancho_util * px_por_cm)
        estampa_h = int(alto_util * px_por_cm)
        pos_x = (view_w - estampa_w) // 2
        pos_y = (view_h - estampa_h) // 2

        svg_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{esp.ancho_cm}cm" height="{esp.alto_cm}cm" viewBox="0 0 {view_w} {view_h}">
    <style>
        .fotopolimero-marco {{ fill: #FFFFFF; stroke: #000000; stroke-width: 4; }}
        .fotopolimero-texto {{ font-family: monospace; font-size: 14px; fill: #000000; }}
        .fotopolimero-estampa {{ filter: grayscale(100%) contrast(200%); }}
    </style>
    <!-- Marco de Fotopolímero (Negro sobre Blanco) -->
    <rect width="{view_w}" height="{view_h}" class="fotopolimero-marco" />
    <text x="20" y="30" class="fotopolimero-texto">FOTOPOLÍMERO INDUSTRIAL - MADYPACK ({esp.ancho_cm}x{esp.alto_cm} cm)</text>
    <text x="20" y="{view_h - 20}" class="fotopolimero-texto">Área Útil: {ancho_util:.1f} x {alto_util:.1f} cm | Manija: {esp.tipo_manija.upper()}</text>

    <!-- Estampa B&N Binarizada -->
    <image x="{pos_x}" y="{pos_y}" width="{estampa_w}" height="{estampa_h}" href="data:image/png;base64,{b64_img}" class="fotopolimero-estampa" preserveAspectRatio="xMidYMid meet" />
</svg>'''
        return svg_xml
