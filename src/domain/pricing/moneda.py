"""Value object de moneda soportada por el cotizador."""

from enum import StrEnum


class Moneda(StrEnum):
    """Monedas reconocidas para referenciar costos."""

    ARS = "ARS"
    USD = "USD"
