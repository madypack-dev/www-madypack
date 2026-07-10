from src.lead.dominio.modelos.lead import Lead


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
