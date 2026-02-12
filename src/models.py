"""Modelos de datos para el scraper de Empresite."""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Empresa:
    """Datos completos de una empresa extraídos de Empresite."""

    # Identificación
    razon_social: str = ""
    cif: str = ""
    forma_juridica: str = ""
    url_ficha: str = ""

    # Clasificación
    sector: str = ""
    actividad: str = ""
    cnae: str = ""
    objeto_social: str = ""
    estado: str = ""

    # Fechas
    fecha_constitucion: str = ""

    # Contacto
    direccion: str = ""
    telefono: str = ""
    email: str = ""
    web: str = ""

    # Datos comerciales
    ventas: str = ""
    num_empleados: str = ""
    participaciones: str = ""
    operaciones_internacionales: str = ""
    grupo_sector: str = ""
    cotiza_bolsa: str = ""

    def to_dict(self) -> dict:
        """Convierte la empresa a diccionario para serialización."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Empresa":
        """Crea una Empresa desde un diccionario."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class ScrapeProgress:
    """Seguimiento del progreso del scraping."""

    total_esperado: int = 0
    empresas_ok: list = field(default_factory=list)
    empresas_error: list = field(default_factory=list)

    @property
    def total_procesadas(self) -> int:
        return len(self.empresas_ok) + len(self.empresas_error)

    @property
    def tasa_exito(self) -> float:
        if self.total_procesadas == 0:
            return 0.0
        return len(self.empresas_ok) / self.total_procesadas * 100

    def add_success(self, empresa: Empresa) -> None:
        self.empresas_ok.append(empresa)

    def add_error(self, url: str, error: str) -> None:
        self.empresas_error.append({"url": url, "error": error})

    def summary(self) -> str:
        lines = [
            f"\n{'='*50}",
            f"  RESUMEN DE SCRAPING",
            f"{'='*50}",
            f"  Empresas encontradas: {self.total_esperado}",
            f"  Fichas procesadas:    {self.total_procesadas}",
            f"  Exitosas:             {len(self.empresas_ok)}",
            f"  Con errores:          {len(self.empresas_error)}",
            f"  Tasa de éxito:        {self.tasa_exito:.1f}%",
            f"{'='*50}",
        ]
        if self.empresas_error:
            lines.append("\n  Errores encontrados:")
            for err in self.empresas_error[:10]:
                lines.append(f"    - {err['url']}: {err['error']}")
            if len(self.empresas_error) > 10:
                lines.append(f"    ... y {len(self.empresas_error) - 10} más")
        return "\n".join(lines)
