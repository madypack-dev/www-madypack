from src.domain.lead.modelos.lead import Lead


def test_crear_lead_entidad():
    lead = Lead.crear(
        nombre="John Doe",
        empresa="Company Inc",
        telefono="+5491125794649",
        email="john@example.com"
    )
    assert lead.nombre == "John Doe"
    assert lead.empresa == "Company Inc"
    assert lead.telefono == "+5491125794649"
    assert lead.email == "john@example.com"
    assert lead.id is None
    assert lead.codigo_referencia.startswith("COT-")
    assert len(lead.codigo_referencia.split("-")) == 3


def test_crear_cotizacion_general():
    lead = Lead.crear_cotizacion_general(
        nombre="Jane Doe",
        empresa="ACME",
        telefono="+5491125794649",
        email="jane@example.com"
    )
    assert lead.codigo_referencia.startswith("COT-GEN-")


def test_crear_contacto():
    lead = Lead.crear_contacto(
        nombre="John Doe",
        empresa="Company Inc",
        telefono="+5491125794649",
        email="john@example.com"
    )
    assert lead.codigo_referencia.startswith("CON-")


def test_crear_emergencia():
    lead = Lead.crear_emergencia(
        nombre="John Doe",
        empresa="Company Inc",
        telefono="+5491125794649",
        email="john@example.com"
    )
    assert lead.codigo_referencia.startswith("COT-ERR-")
