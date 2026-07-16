"""Value object de moneda soportada por el cotizador."""

from enum import Enum


class Moneda(str, Enum):
    """Monedas reconocidas para referenciar costos."""

    ARS = "ARS"
    USD = "USD"
