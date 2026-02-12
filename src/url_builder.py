"""Construcción de URLs para Empresite con filtros combinables."""

from typing import Optional
from src.config import BASE_URL


def build_listing_url(
    actividad_slug: Optional[str] = None,
    provincia_slug: Optional[str] = None,
    localidad_slug: Optional[str] = None,
    page: int = 1,
) -> str:
    """Construye la URL del listado con filtros combinados.

    Patrones de URL descubiertos:
      Solo actividad:     /Actividad/PESCA/
      Solo provincia:     /provincia/JAEN/
      Combinado:          /Actividad/PESCA/provincia/PONTEVEDRA/
      Con localidad:      /Actividad/PESCA/localidad/VIGO-PONTEVEDRA/
      Solo localidad:     /localidad/UBEDA-JAEN/
      Con paginación:     .../PgNum-2/

    Args:
        actividad_slug: Slug de actividad en mayúsculas (ej: "PESCA").
        provincia_slug: Slug de provincia en mayúsculas (ej: "JAEN").
        localidad_slug: Slug de localidad completo (ej: "UBEDA-JAEN").
        page: Número de página (1 = primera, sin sufijo PgNum).

    Returns:
        URL completa del listado.

    Raises:
        ValueError: Si no se especifica ningún filtro.
    """
    if not any([actividad_slug, provincia_slug, localidad_slug]):
        raise ValueError("Debe especificar al menos un filtro (actividad, provincia o localidad)")

    parts = [BASE_URL]

    # Actividad va primero en la URL
    if actividad_slug:
        parts.append(f"/Actividad/{actividad_slug}")

    # Localidad tiene prioridad sobre provincia (es más específica)
    if localidad_slug:
        parts.append(f"/localidad/{localidad_slug}")
    elif provincia_slug:
        parts.append(f"/provincia/{provincia_slug}")

    url = "".join(parts) + "/"

    # Paginación: página 1 no lleva sufijo, página 2+ usa /PgNum-N/
    if page > 1:
        url += f"PgNum-{page}/"

    return url


def build_company_url(slug: str) -> str:
    """Construye la URL de la ficha de una empresa.

    Args:
        slug: Slug de la empresa (ej: "NOVANTOLIN-PESCA.html" o URL completa).

    Returns:
        URL completa de la ficha.
    """
    if slug.startswith("http"):
        return slug
    return f"{BASE_URL}/{slug}"
