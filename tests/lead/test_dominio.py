from datetime import datetime
from src.domain.lead.modelos.lead import Lead


def test_crear_lead_entidad():
    fecha_fija = datetime(2026, 7, 10, 12, 0, 0)
    lead = Lead.crear(
        nombre="John Doe",
        empresa="Company Inc",
        telefono="+5491125794649",
        email="john@example.com",
        fecha=fecha_fija,
        sufijo="ABCD"
    )
    assert lead.nombre == "John Doe"
    assert lead.empresa == "Company Inc"
    assert lead.telefono == "+5491125794649"
    assert lead.email == "john@example.com"
    assert lead.id is None
    assert lead.codigo_referencia == "COT-20260710-ABCD"


def test_crear_cotizacion_general():
    fecha_fija = datetime(2026, 7, 10, 12, 0, 0)
    lead = Lead.crear_cotizacion_general(
        nombre="Jane Doe",
        empresa="ACME",
        telefono="+5491125794649",
        email="jane@example.com",
        fecha=fecha_fija,
        sufijo="EFGH"
    )
    assert lead.codigo_referencia == "COT-GEN-20260710-EFGH"


def test_crear_contacto():
    fecha_fija = datetime(2026, 7, 10, 12, 0, 0)
    lead = Lead.crear_contacto(
        nombre="John Doe",
        empresa="Company Inc",
        telefono="+5491125794649",
        email="john@example.com",
        fecha=fecha_fija,
        sufijo="IJKL"
    )
    assert lead.codigo_referencia == "CON-20260710-IJKL"


def test_crear_emergencia():
    lead = Lead.crear_emergencia(
        nombre="John Doe",
        empresa="Company Inc",
        telefono="+5491125794649",
        email="john@example.com",
        sufijo="MNOP"
    )
    assert lead.codigo_referencia == "COT-ERR-MNOP"

