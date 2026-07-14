"""Adapter de infraestructura que genera el PDF de presupuesto con ReportLab + svglib."""

from datetime import timedelta
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from src.domain.quote.visual_identity import IdentidadVisual
from src.domain.quote.quote import LineaPresupuesto, Presupuesto
from src.domain.quote.pdf_generator import IGeneradorDocumentoPresupuesto


class GeneradorPresupuestoPDFReportLab(IGeneradorDocumentoPresupuesto):
    """Genera un PDF de presupuesto usando ReportLab posicionalmente."""

    MARGEN = 20 * mm
    ANCHO_LINEA = 0.5
    COLOR_PRINCIPAL = colors.HexColor("#1a1a1a")
    COLOR_ACENTO = colors.HexColor("#333333")
    COLOR_FONDO_CABECERA = colors.HexColor("#f5f5f5")

    def generar(self, presupuesto: Presupuesto, identidad_visual: IdentidadVisual) -> bytes:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        ancho, alto = A4
        x = self.MARGEN
        y = alto - self.MARGEN

        styles = getSampleStyleSheet()
        estilo_normal = ParagraphStyle(
            "normal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=self.COLOR_PRINCIPAL,
        )
        estilo_titulo = ParagraphStyle(
            "titulo",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=self.COLOR_PRINCIPAL,
            alignment=1,  # centrado
        )
        estilo_subtitulo = ParagraphStyle(
            "subtitulo",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=self.COLOR_ACENTO,
        )
        estilo_pequeno = ParagraphStyle(
            "pequeno",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.grey,
        )

        # --- Encabezado: logo + brand ---
        y = self._dibujar_encabezado(c, x, y, identidad_visual, ancho)

        # --- Título y metadatos ---
        y -= 8 * mm
        titulo = Paragraph("PRESUPUESTO", estilo_titulo)
        _, h = titulo.wrapOn(c, ancho - 2 * self.MARGEN, 30 * mm)
        titulo.drawOn(c, x, y - h)
        y -= h + 4 * mm

        fecha_emision = presupuesto.fecha_emision.strftime("%d/%m/%Y")
        fecha_vencimiento = (
            presupuesto.fecha_emision + timedelta(days=presupuesto.validez_dias)
        ).strftime("%d/%m/%Y")
        meta_texto = (
            f"<b>Fecha de emisión:</b> {fecha_emision}<br/>"
            f"<b>Válido hasta:</b> {fecha_vencimiento} ({presupuesto.validez_dias} días)"
        )
        meta = Paragraph(meta_texto, estilo_normal)
        _, h = meta.wrapOn(c, ancho - 2 * self.MARGEN, 20 * mm)
        meta.drawOn(c, x, y - h)
        y -= h + 6 * mm

        # --- Datos del solicitante ---
        y = self._dibujar_datos_solicitante(c, x, y, presupuesto, ancho, estilo_subtitulo, estilo_normal)

        # --- Tabla de líneas ---
        y = self._dibujar_tabla_lineas(c, x, y, presupuesto.lineas, ancho, estilo_normal, estilo_subtitulo)

        # --- Total ---
        y -= 4 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(ancho - self.MARGEN, y, f"TOTAL ESTIMADO: {self._formatear_moneda(presupuesto.total_estimado)}")
        y -= 8 * mm

        # --- Condiciones comerciales ---
        y = self._dibujar_condiciones(c, x, y, presupuesto.condiciones_comerciales, ancho, estilo_subtitulo, estilo_normal)

        # --- Pie ---
        self._dibujar_pie(c, x, identidad_visual, ancho, estilo_pequeno)

        c.save()
        buffer.seek(0)
        return buffer.read()

    def _dibujar_encabezado(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        identidad: IdentidadVisual,
        ancho: float,
    ) -> float:
        alto_caja = 22 * mm
        c.setFillColor(self.COLOR_FONDO_CABECERA)
        c.rect(x, y - alto_caja, ancho - 2 * self.MARGEN, alto_caja, fill=1, stroke=0)

        x_logo = x + 4 * mm
        y_logo = y - 4 * mm
        x_texto = x_logo
        if identidad.logo_path and Path(identidad.logo_path).is_file():
            try:
                drawing = svg2rlg(identidad.logo_path)
                if drawing:
                    max_ancho = 45 * mm
                    max_alto = 14 * mm
                    escala = min(max_ancho / drawing.width, max_alto / drawing.height)
                    drawing.width = int(drawing.width * escala)
                    drawing.height = int(drawing.height * escala)
                    drawing.scale(escala, escala)  # type: ignore[arg-type]
                    renderPDF.draw(drawing, c, x_logo, y_logo - drawing.height)
                    x_texto = x_logo + drawing.width + 6 * mm
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(self.COLOR_PRINCIPAL)
        c.drawString(x_texto, y - 8 * mm, identidad.brand)
        if identidad.tagline:
            c.setFont("Helvetica", 10)
            c.setFillColor(self.COLOR_ACENTO)
            c.drawString(x_texto, y - 13 * mm, identidad.tagline)

        return y - alto_caja

    def _dibujar_datos_solicitante(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        presupuesto: Presupuesto,
        ancho: float,
        estilo_subtitulo: ParagraphStyle,
        estilo_normal: ParagraphStyle,
    ) -> float:
        titulo = Paragraph("Datos del solicitante", estilo_subtitulo)
        _, h = titulo.wrapOn(c, ancho - 2 * self.MARGEN, 10 * mm)
        titulo.drawOn(c, x, y - h)
        y -= h + 2 * mm

        datos = presupuesto.datos_solicitante
        lineas = [
            f"<b>Nombre:</b> {datos.nombre or 'No informado'}",
            f"<b>Email:</b> {datos.email}",
            f"<b>Teléfono:</b> {datos.telefono}",
            f"<b>Empresa:</b> {datos.empresa or 'No informada'}",
        ]
        if datos.mensaje:
            lineas.append(f"<b>Consulta:</b> {datos.mensaje}")

        texto = "<br/>".join(lineas)
        parrafo = Paragraph(texto, estilo_normal)
        ancho_caja = ancho - 2 * self.MARGEN
        _, h = parrafo.wrapOn(c, ancho_caja, 60 * mm)

        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(self.ANCHO_LINEA)
        c.roundRect(x, y - h - 4 * mm, ancho_caja, h + 8 * mm, 3 * mm, fill=0, stroke=1)

        parrafo.drawOn(c, x + 4 * mm, y - h - 2 * mm)
        return y - h - 10 * mm

    def _dibujar_tabla_lineas(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        lineas: list[LineaPresupuesto],
        ancho: float,
        estilo_normal: ParagraphStyle,
        estilo_subtitulo: ParagraphStyle,
    ) -> float:
        titulo = Paragraph("Detalle de la cotización", estilo_subtitulo)
        _, h = titulo.wrapOn(c, ancho - 2 * self.MARGEN, 10 * mm)
        titulo.drawOn(c, x, y - h)
        y -= h + 2 * mm

        ancho_tabla = ancho - 2 * self.MARGEN
        col_producto = ancho_tabla * 0.45
        col_cantidad = ancho_tabla * 0.15
        col_unitario = ancho_tabla * 0.20
        col_subtotal = ancho_tabla * 0.20

        encabezados = [
            Paragraph("<b>Producto / Servicio</b>", estilo_normal),
            Paragraph("<b>Cantidad</b>", estilo_normal),
            Paragraph("<b>P. unitario</b>", estilo_normal),
            Paragraph("<b>Subtotal</b>", estilo_normal),
        ]
        datos_tabla = [encabezados]

        for linea in lineas:
            nombre = Paragraph(f"<b>{linea.nombre}</b><br/>{linea.descripcion}", estilo_normal)
            datos_tabla.append([
                nombre,
                Paragraph(f"{linea.cantidad:,} {linea.unidad}", estilo_normal),
                Paragraph(self._formatear_moneda(linea.precio_unitario_estimado), estilo_normal),
                Paragraph(self._formatear_moneda(linea.subtotal), estilo_normal),
            ])

        tabla = Table(datos_tabla, colWidths=[col_producto, col_cantidad, col_unitario, col_subtotal])
        tabla.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), self.COLOR_FONDO_CABECERA),
                ("TEXTCOLOR", (0, 0), (-1, 0), self.COLOR_PRINCIPAL),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        _, h = tabla.wrapOn(c, ancho_tabla, 200 * mm)
        tabla.drawOn(c, x, y - h)
        return y - h

    def _dibujar_condiciones(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        condiciones: list[str],
        ancho: float,
        estilo_subtitulo: ParagraphStyle,
        estilo_normal: ParagraphStyle,
    ) -> float:
        titulo = Paragraph("Condiciones comerciales", estilo_subtitulo)
        _, h = titulo.wrapOn(c, ancho - 2 * self.MARGEN, 10 * mm)
        titulo.drawOn(c, x, y - h)
        y -= h + 2 * mm

        items = [f"• {condicion}" for condicion in condiciones]
        texto = "<br/>".join(items)
        parrafo = Paragraph(texto, estilo_normal)
        _, h = parrafo.wrapOn(c, ancho - 2 * self.MARGEN, 80 * mm)
        parrafo.drawOn(c, x, y - h)
        return y - h

    def _dibujar_pie(
        self,
        c: canvas.Canvas,
        x: float,
        identidad: IdentidadVisual,
        ancho: float,
        estilo_pequeno: ParagraphStyle,
    ) -> None:
        y_pie = 12 * mm
        partes = []
        if identidad.direccion:
            partes.append(identidad.direccion)
        if identidad.email:
            partes.append(f"Email: {identidad.email}")
        if identidad.telefono:
            partes.append(f"Tel: {identidad.telefono}")
        if identidad.whatsapp:
            partes.append(f"WhatsApp: {identidad.whatsapp}")
        if identidad.url:
            partes.append(identidad.url)

        texto = " | ".join(partes)
        parrafo = Paragraph(texto, estilo_pequeno)
        _, h = parrafo.wrapOn(c, ancho - 2 * self.MARGEN, 15 * mm)
        parrafo.drawOn(c, x, y_pie)

    def _formatear_moneda(self, valor: float) -> str:
        if valor > 0.0:
            return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return "A cotizar"
