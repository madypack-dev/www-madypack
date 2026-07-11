def formatear_precio(precio_total: float) -> str:
    """Formatea un precio numérico al formato regional local."""
    if precio_total > 0:
        return f"$ {precio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "A cotizar"


def formatear_unidades(total_bolsas: int) -> str:
    """Formatea la cantidad de unidades/bolsas con separador de miles local."""
    return f"{total_bolsas:,} unidades".replace(",", ".")
