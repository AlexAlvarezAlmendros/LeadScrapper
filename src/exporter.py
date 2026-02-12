"""Exportación de datos a JSON y CSV."""

import csv
import json
import os
from datetime import datetime
from typing import Optional

from src.models import Empresa


# Orden de columnas para el CSV
CSV_COLUMNS = [
    "razon_social",
    "cif",
    "forma_juridica",
    "sector",
    "actividad",
    "cnae",
    "estado",
    "fecha_constitucion",
    "objeto_social",
    "direccion",
    "telefono",
    "email",
    "web",
    "ventas",
    "num_empleados",
    "participaciones",
    "operaciones_internacionales",
    "grupo_sector",
    "cotiza_bolsa",
    "url_ficha",
]


def save_to_json(empresas: list[Empresa], filepath: str) -> str:
    """Guarda la lista de empresas en formato JSON.

    Args:
        empresas: Lista de objetos Empresa.
        filepath: Ruta del archivo de salida.

    Returns:
        Ruta absoluta del archivo generado.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    data = [e.to_dict() for e in empresas]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return os.path.abspath(filepath)


def json_to_csv(json_path: str, csv_path: Optional[str] = None) -> str:
    """Convierte un archivo JSON de empresas a CSV.

    Usa separador ';' para compatibilidad con Excel en español.

    Args:
        json_path: Ruta del archivo JSON de origen.
        csv_path: Ruta del CSV de salida (por defecto, mismo nombre con .csv).

    Returns:
        Ruta absoluta del archivo CSV generado.
    """
    if csv_path is None:
        csv_path = json_path.rsplit(".", 1)[0] + ".csv"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_COLUMNS,
            delimiter=";",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    return os.path.abspath(csv_path)


def export_all(
    empresas: list[Empresa],
    output_dir: str = "output",
    filename: Optional[str] = None,
) -> tuple[str, str]:
    """Exporta empresas a JSON y CSV.

    Args:
        empresas: Lista de objetos Empresa.
        output_dir: Directorio de salida.
        filename: Nombre base del archivo (sin extensión).
                  Si no se proporciona, genera uno con timestamp.

    Returns:
        Tupla (ruta_json, ruta_csv).
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"empresas_{timestamp}"

    json_path = os.path.join(output_dir, f"{filename}.json")
    csv_path = os.path.join(output_dir, f"{filename}.csv")

    save_to_json(empresas, json_path)
    json_to_csv(json_path, csv_path)

    return os.path.abspath(json_path), os.path.abspath(csv_path)
