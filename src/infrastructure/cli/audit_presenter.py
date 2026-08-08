"""Presentador visual de auditoría CLI utilizando la librería Rich.

Ubicado en la capa de Infraestructura (src/infrastructure/cli/audit_presenter.py),
este módulo formatea paneles, tablas de alto contraste y métricas estadísticas.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def presentar_perfil_empresa(empresa_data: dict[str, Any]) -> None:
    """Renderiza un panel destacado con los datos fiscales de la empresa conectada."""
    nombre = empresa_data.get("nombreEmpresa") or empresa_data.get("nombre", "Desconocido")
    cuit = empresa_data.get("cuit") or empresa_data.get("identificacion_tributaria", "N/A")
    telefono = empresa_data.get("telefono", "N/A")
    email = empresa_data.get("email", "N/A")
    actividad = empresa_data.get("fechaInicioActividad", "N/A")

    contenido = Text()
    contenido.append("🏢 Razón Social: ", style="bold cyan")
    contenido.append(f"{nombre}\n", style="bold white")
    contenido.append("📜 CUIT / Identificación: ", style="bold cyan")
    contenido.append(f"{cuit}\n", style="bold yellow")
    contenido.append("📞 Teléfono: ", style="bold cyan")
    contenido.append(f"{telefono}  |  ", style="white")
    contenido.append("✉️ Email: ", style="bold cyan")
    contenido.append(f"{email}\n", style="white")
    contenido.append("📅 Inicio Actividades: ", style="bold cyan")
    contenido.append(f"{actividad}", style="dim white")

    panel = Panel(
        contenido,
        title="[bold green] Perfil de Empresa Autenticada en Xubio ERP [/bold green]",
        border_style="green",
    )
    console.print(panel)


def presentar_listas_precio(listas_data: list[dict[str, Any]]) -> None:
    """Renderiza una tabla estilizada con el resumen de listas de precio activas en Xubio."""
    table = Table(
        title="📋 Listas de Precios Registradas en Xubio ERP",
        border_style="blue",
        header_style="bold magenta",
    )
    table.add_column("ID Lista", justify="right", style="cyan", no_wrap=True)
    table.add_column("Nombre", style="bold white")
    table.add_column("Descripción", style="dim white")
    table.add_column("Tipo", style="yellow")
    table.add_column("Estado", justify="center")
    table.add_column("Ítems Registrados", justify="right", style="green")

    for item_lista in listas_data:
        list_id = str(item_lista.get("listaPrecioID") or item_lista.get("id", "N/A"))
        nombre = item_lista.get("nombre", "Sin Nombre")
        descripcion = item_lista.get("descripcion") or "-"
        tipo = "Compra" if item_lista.get("tipo") == 2 else "Venta"
        activo = "🟢 Activa" if item_lista.get("activo", True) else "🔴 Inactiva"
        items_count = str(len(item_lista.get("listaPrecioItem", [])))

        table.add_row(list_id, nombre, descripcion, tipo, activo, items_count)

    console.print(table)


def presentar_productos_stock(productos: list[dict[str, Any]]) -> None:
    """Renderiza una tabla de stock e insumos, destacando en rojo productos con precio $0,00."""
    table = Table(
        title="📦 Muestra de Productos y Stock en Xubio ERP",
        border_style="magenta",
        header_style="bold yellow",
    )
    table.add_column("Código / SKU", style="cyan")
    table.add_column("Nombre de Producto", style="bold white")
    table.add_column("Stock", justify="right")
    table.add_column("Precio Registrado", justify="right")
    table.add_column("Diagnóstico Tarifario", style="bold")

    for p in productos:
        codigo = p.get("codigo") or p.get("usrcode") or "-"
        nombre = p.get("nombre") or p.get("descripcion") or "Sin Nombre"
        stock = f"{p.get('stock', 0.0):.2f}"
        precio = p.get("precio", 0.0)

        if precio > 0:
            precio_str = f"[bold green]${precio:.2f} ARS[/bold green]"
            diag = "[bold green]✅ Tarifa Válida[/bold green]"
        elif "BOBINA" in nombre.upper() or "KRAFT" in nombre.upper() or codigo == "BOBMAR100":
            precio_str = "[bold red]$0.00 ARS[/bold red]"
            diag = "[bold red]🚨 INSUMO CLAVE SIN PRECIO (BOBMAR100)[/bold red]"
        else:
            precio_str = "[dim]$0.00 ARS[/dim]"
            diag = "[dim]Sin precio asignado[/dim]"

        table.add_row(codigo, nombre, stock, precio_str, diag)

    console.print(table)


def presentar_analisis_anomalias(reporte_anomalias: dict[str, Any]) -> None:
    """Renderiza el reporte estadístico de anomalías (Mediana + MAD + Unidades)."""
    mediana = reporte_anomalias.get("mediana_ars_kg", 0.0)
    mad = reporte_anomalias.get("mad", 0.0)
    cota = reporte_anomalias.get("cota_tolerancia", 0.0)
    anomalias = reporte_anomalias.get("anomalias", [])
    falsos_negativos = reporte_anomalias.get("falsos_negativos", [])

    content = Text()
    content.append("📊 Mediana Estadística Base: ", style="bold cyan")
    content.append(f"${mediana:.2f} ARS / kg\n", style="bold green")
    content.append("📐 MAD (Desviación Absoluta Mediana): ", style="bold cyan")
    content.append(f"${mad:.2f} ARS / kg\n", style="bold yellow")
    content.append("🛡️ Cota Máxima Tolerada (k * MAD): ", style="bold cyan")
    content.append(f"${cota:.2f} ARS / kg\n\n", style="bold magenta")

    if anomalias:
        content.append(f"🚨 ANOMALÍAS DETECTADAS ({len(anomalias)}):\n", style="bold red")
        for a in anomalias:
            content.append(
                f"  • {a['codigo']}: ${a['precio_kg']:.2f}/kg (Desviación de ${a['desviacion_mediana']:.2f})\n",
                style="red",
            )
    else:
        content.append("✅ Sin anomalías numéricas detectadas en precios.\n", style="bold green")

    if falsos_negativos:
        content.append(
            f"\nℹ️ POSIBLES FALSOS NEGATIVOS / FALTAS DE MAPEO ({len(falsos_negativos)}):\n",
            style="bold yellow",
        )
        for fn in falsos_negativos:
            content.append(f"  • {fn['codigo']}: {fn['motivo']}\n", style="yellow")

    panel = Panel(
        content,
        title="[bold yellow] Análisis Estadístico de Anomalías (Mediana + MAD) [/bold yellow]",
        border_style="yellow",
    )
    console.print(panel)


def presentar_casos_zero_trust(casos_sanitizados: list[dict[str, Any]]) -> None:
    """Renderiza el reporte de pruebas defensivas Zero-Trust."""
    table = Table(
        title="🛡️ Resultados de Sanitización Defensiva Zero-Trust",
        border_style="cyan",
        header_style="bold cyan",
    )
    table.add_column("Caso", justify="center", style="dim white")
    table.add_column("Entrada Cruda (Xubio)", style="red")
    table.add_column("Salida Sanitizada (Madypack)", style="bold green")
    table.add_column("Estado de Seguridad", style="bold yellow")

    for idx, c in enumerate(casos_sanitizados, 1):
        raw_str = str(c.get("entrada"))
        clean_str = f"codigo='{c.get('codigo')}', monto={c.get('monto')}, fecha={c.get('fecha')}"
        estado = "🛡️ Bloqueado / Sanitizado"
        table.add_row(str(idx), raw_str, clean_str, estado)

    console.print(table)
