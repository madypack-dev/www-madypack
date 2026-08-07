"""Adaptador que genera la previsualización 2D (mockup) paramétrica de la bolsa armada en SVG."""

import base64

from src.domain.customization.customization import PersonalizacionBolsa
from src.domain.customization.customization_ports import IGeneradorMockupBolsaSVG


class GeneradorMockupBolsaSVGAdapter(IGeneradorMockupBolsaSVG):
    """Adaptador que renderiza una bolsa armada con pliegues, sombras, tipo de manija y estampa personalizada."""

    def generar_svg_mockup(self, personalizacion: PersonalizacionBolsa) -> str:
        esp = personalizacion.especificacion
        ancho_util, alto_util = personalizacion.calcular_area_util_impresion()

        # Canvas proporcional (350x450 px)
        view_w = 400
        view_h = 500

        # Dimensiones de la bolsa en el gráfico
        bolsa_w = 260
        bolsa_h = 320
        pos_x = (view_w - bolsa_w) // 2
        pos_y = (view_h - bolsa_h) // 2 + 30

        # Codificar imagen de estampa
        b64_img = base64.b64encode(personalizacion.diseno.contenido_bytes).decode("utf-8")
        mime = personalizacion.diseno.mime_type or "image/png"

        # Trazado SVG de la manija según el tipo seleccionado
        manija_svg = ""
        if esp.tipo_manija == "manija_retorcida":
            manija_svg = f'''
            <path d="M {pos_x + 70} {pos_y} Q {pos_x + 70} {pos_y - 80} {pos_x + 95} {pos_y - 80} T {pos_x + 120} {pos_y}" fill="none" stroke="{esp.color_papel}" stroke-width="12" stroke-linecap="round" />
            <path d="M {pos_x + 140} {pos_y} Q {pos_x + 140} {pos_y - 80} {pos_x + 165} {pos_y - 80} T {pos_x + 190} {pos_y}" fill="none" stroke="{esp.color_papel}" stroke-width="12" stroke-linecap="round" />
            '''
        elif esp.tipo_manija == "manija_plana":
            manija_svg = f'''
            <path d="M {pos_x + 65} {pos_y} L {pos_x + 65} {pos_y - 60} L {pos_x + 115} {pos_y - 60} L {pos_x + 115} {pos_y}" fill="none" stroke="{esp.color_papel}" stroke-width="16" />
            <path d="M {pos_x + 145} {pos_y} L {pos_x + 145} {pos_y - 60} L {pos_x + 195} {pos_y - 60} L {pos_x + 195} {pos_y}" fill="none" stroke="{esp.color_papel}" stroke-width="16" />
            '''

        # Tamaño y posición de la estampa
        estampa_w = 160
        estampa_h = 160
        estampa_x = pos_x + (bolsa_w - estampa_w) // 2
        estampa_y = pos_y + (bolsa_h - estampa_h) // 2 + 10

        svg_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 {view_w} {view_h}">
    <defs>
        <!-- Sombra paralela para la bolsa -->
        <filter id="shadow" x="-10%" y="-10%" width="130%" height="130%">
            <feDropShadow dx="4" dy="10" stdDeviation="8" flood-opacity="0.2" flood-color="#000000" />
        </filter>
        <!-- Tinta personalizada sobre el logo -->
        <filter id="ink-color">
            <feFlood flood-color="{esp.color_tinta}" result="flood" />
            <feComposite in="flood" in2="SourceAlpha" operator="in" />
        </filter>
    </defs>

    <!-- Fondo de vista previa -->
    <rect width="{view_w}" height="{view_h}" fill="#F4F5F7" rx="12" />

    <!-- Manijas -->
    {manija_svg}

    <!-- Cuerpo de la Bolsa de Papel -->
    <rect x="{pos_x}" y="{pos_y}" width="{bolsa_w}" height="{bolsa_h}" fill="{esp.color_papel}" filter="url(#shadow)" rx="4" />
    
    <!-- Pliegues y textura de la bolsa -->
    <line x1="{pos_x}" y1="{pos_y + 15}" x2="{pos_x + bolsa_w}" y2="{pos_y + 15}" stroke="#000000" stroke-opacity="0.1" stroke-width="2" />
    <path d="M {pos_x} {pos_y} L {pos_x + 30} {pos_y + bolsa_h} L {pos_x} {pos_y + bolsa_h} Z" fill="#000000" fill-opacity="0.05" />

    <!-- Estampa con Tinta Personalizada -->
    <image x="{estampa_x}" y="{estampa_y}" width="{estampa_w}" height="{estampa_h}" href="data:{mime};base64,{b64_img}" filter="url(#ink-color)" preserveAspectRatio="xMidYMid meet" />

    <!-- Etiqueta de dimensiones -->
    <text x="{view_w // 2}" y="{view_h - 20}" font-family="sans-serif" font-size="13" font-weight="bold" fill="#555555" text-anchor="middle">
        Bolsa {esp.ancho_cm:.0f}x{esp.alto_cm:.0f} cm ({esp.color_papel})
    </text>
</svg>'''
        return svg_xml
