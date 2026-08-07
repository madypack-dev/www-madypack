# language: es
Característica: Verificación BDD de Reglas de Arquitectura Limpia
  Como arquitecto del proyecto Madypack
  Quiero asegurar que los módulos del dominio no importen infraestructura ni frameworks web
  Para proteger la lógica de negocio de acoplamientos indeseados

  Escenario: Dominio libre de dependencias de infraestructura
    Dado la estructura actual del paquete "src/domain"
    Cuando ejecuto la inspección sintáctica de dependencias
    Entonces no debe detectarse ninguna importación proveniente de "fastapi", "httpx" ni "infrastructure"
