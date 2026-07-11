import json
from pathlib import Path
from src.domain.quote.quote import Presupuesto
from src.domain.quote.quote_repository import IQuoteRepository

class JsonQuoteRepository(IQuoteRepository):
    """Implementación de IQuoteRepository para guardar presupuestos en formato JSON de manera local."""

    def __init__(self, data_dir: str = "data/presupuestos"):
        self.data_dir = Path(data_dir)

    def guardar(self, ref: str, presupuesto: Presupuesto) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.data_dir / f"{ref}.json"
        file_path.write_text(presupuesto.model_dump_json(indent=2), encoding="utf-8")

    def obtener_por_referencia(self, ref: str) -> Presupuesto | None:
        file_path = self.data_dir / f"{ref}.json"
        if not file_path.exists():
            return None
        try:
            datos_json = json.loads(file_path.read_text(encoding="utf-8"))
            return Presupuesto(**datos_json)
        except Exception:
            return None
