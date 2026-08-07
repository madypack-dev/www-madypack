import pytest

from src.adapters.gateways.null_erp_gateway import NullErpGateway
from src.application.erp.use_cases import CasoUsoObtenerEmpresaERP, CasoUsoVerificarConexionERP
from src.domain.erp.entities import EmpresaERP, EstadoConexionERP


@pytest.mark.asyncio
async def test_caso_uso_verificar_conexion_erp_con_null_gateway():
    gateway = NullErpGateway()
    use_case = CasoUsoVerificarConexionERP(gateway)

    resultado = await use_case.ejecutar()

    assert isinstance(resultado, EstadoConexionERP)
    assert resultado.activo is True
    assert resultado.proveedor == "NullERP"


@pytest.mark.asyncio
async def test_caso_uso_obtener_empresa_erp_con_null_gateway():
    gateway = NullErpGateway()
    use_case = CasoUsoObtenerEmpresaERP(gateway)

    empresa = await use_case.ejecutar()

    assert isinstance(empresa, EmpresaERP)
    assert empresa.id == "0"
    assert empresa.nombre == "Empresa Dummy Madypack"
