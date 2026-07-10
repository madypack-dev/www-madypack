"""Adaptador de contingencia que persiste leads fallidos en archivo local."""

import json
import os
from datetime import datetime
from pathlib import Path

from src.lead.dominio.modelos.lead import Lead
from src.presupuesto.dominio.puertos.registro_fallback import IRegistroFallbackLead


class RegistroFallbackArchivo(IRegistroFallbackLead):
    """Escribe leads fallidos en un archivo JSONLines como contingencia."""

    def __init__(self, file_path: str = "logs/failed_leads.log"):
        self.file_path = Path(file_path)

    def guardar(self, lead: Lead, error_msg: str) -> None:
        fallback_data = {
            "timestamp": datetime.now().isoformat(),
            "lead_id": lead.id,
            "codigo_referencia": lead.codigo_referencia,
            "nombre": lead.nombre,
            "empresa": lead.empresa,
            "email": str(lead.email),
            "telefono": lead.telefono,
            "error": error_msg,
        }
        self._escribir_linea(json.dumps(fallback_data))

    def _escribir_linea(self, linea: str) -> None:
        os.makedirs(self.file_path.parent, exist_ok=True)
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
