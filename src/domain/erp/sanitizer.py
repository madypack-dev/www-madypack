"""Sanitizador defensivo Zero-Trust para respuestas de la API de Xubio ERP v1.1."""

import re
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from src.domain.pricing.concepto_tarifa import ConceptoTarifa
from src.domain.pricing.moneda import Moneda

_TAG_RE = re.compile(r"<[^>]+>")


def sanitizar_texto(val: Any, max_len: int = 255, default: str = "") -> str:
    """Sanitiza cualquier valor de texto eliminando tags HTML/XSS, espacios sobrantes y acortando longitud."""
    if val is None:
        return default
    text = str(val)
    text = _TAG_RE.sub("", text)  # Elimina etiquetas HTML/XSS
    text = text.strip()
    return text[:max_len] if text else default


def sanitizar_monto(val: Any, min_val: float = 0.0, default: float = 0.0) -> float:
    """Sanitiza montos numéricos asegurando que sean flotantes válidos (no NaN/Inf) y no negativos."""
    try:
        num = float(val)
        if num != num or num == float("inf") or num == float("-inf"):
            return default
        return max(min_val, num)
    except (ValueError, TypeError):
        return default


def sanitizar_fecha(val: Any) -> date:
    """Parsea cadenas de fecha ISO o de Xubio con resguardo automático a date.today()."""
    if not val:
        return date.today()
    try:
        val_str = str(val).strip().split("T")[0]
        return date.fromisoformat(val_str)
    except Exception:
        return date.today()


def sanitizar_moneda(val: Any) -> Moneda:
    """Sanitiza identificadores o códigos de moneda con fallback a Moneda.ARS."""
    if not val:
        return Moneda.ARS
    val_str = str(val).upper().strip()
    if "USD" in val_str or "DOLAR" in val_str or val_str == "2":
        return Moneda.USD
    return Moneda.ARS


class TarifaSanitizada(BaseModel):
    """Value Object Pydantic para representar un concepto de tarifa sanitizado desde el ERP."""

    model_config = ConfigDict(frozen=True)

    nombre: str
    monto: float
    moneda: Moneda = Moneda.ARS
    fecha: date = Field(default_factory=date.today)

    def a_concepto_tarifa(self) -> ConceptoTarifa:
        """Convierte la tarifa sanitizada al Value Object de dominio ConceptoTarifa."""
        return ConceptoTarifa(
            nombre=self.nombre,
            monto=self.monto,
            moneda=self.moneda,
            fecha=self.fecha,
        )


def sanitizar_item_tarifa(raw_item: Any) -> ConceptoTarifa | None:
    """Procesa un diccionario crudo devuelto por Xubio y devuelve un ConceptoTarifa sanitizado o None si es inválido."""
    if not isinstance(raw_item, dict):
        return None


    raw_codigo = raw_item.get("codigo") or raw_item.get("nombre") or raw_item.get("usrcode")
    codigo = sanitizar_texto(raw_codigo, max_len=100)
    if not codigo:
        return None

    raw_precio = raw_item.get("precio") or raw_item.get("monto") or raw_item.get("precioUltCompra")
    monto = sanitizar_monto(raw_precio)
    moneda = sanitizar_moneda(raw_item.get("moneda"))
    fecha = sanitizar_fecha(raw_item.get("fecha"))

    tarifa = TarifaSanitizada(
        nombre=codigo,
        monto=monto,
        moneda=moneda,
        fecha=fecha,
    )
    return tarifa.a_concepto_tarifa()
