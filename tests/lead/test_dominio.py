from src.lead.dominio.modelos.lead import Lead
from src.lead.dominio.modelos.eventos import LeadCreado
import uuid
from datetime import datetime

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

def test_evento_lead_creado():
    ev_id = uuid.uuid4()
    now = datetime.now()
    evento = LeadCreado(
        id_evento=ev_id,
        ocurrido_en=now,
        lead_id="123",
        nombre="John",
        empresa="Company",
        telefono="+549",
        email="john@example.com",
        codigo_referencia="COT-123",
        resumen_lineas=2
    )
    assert evento.lead_id == "123"
    assert evento.resumen_lineas == 2
