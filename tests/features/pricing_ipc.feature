# language: es
Característica: Actualización de Tarifas por IPC y Cotización
  Como motor de precios de Madypack
  Quiero actualizar el valor base de las tarifas en ARS usando el IPC acumulado
  Para calcular presupuestos precisos a valor presente sin modificar la base de datos

  Escenario: Ajuste por IPC acumulado positivo
    Dado un valor de tarifa base de 100.0 ARS registrado en fecha "2024-01-01"
    Y un factor IPC acumulado de 1.25 hasta la fecha "2024-06-01"
    Cuando se calcula el importe actualizado a valor presente
    Entonces el precio unitario resultante debe ser 125.0 ARS
