"""CLI interactivo para el scraper de Empresite."""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

from src.config import ACTIVIDADES, PROVINCIAS
from src.exporter import export_all
from src.scraper import EmpresiteScraper


def clear_screen():
    """Limpia la pantalla de la consola."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Muestra el banner del programa."""
    print("""
╔══════════════════════════════════════════════════════════╗
║            LEADSCRAPPER - Empresite Scraper              ║
║     Extractor de datos de empresas españolas             ║
╚══════════════════════════════════════════════════════════╝
    """)


def print_menu(title: str, options: list[str], allow_skip: bool = False) -> int:
    """Muestra un menú numerado y devuelve la selección.

    Args:
        title: Título del menú.
        options: Lista de opciones.
        allow_skip: Si True, permite saltar con 0.

    Returns:
        Índice seleccionado (0-based), o -1 si se salta.
    """
    print(f"\n  {title}")
    print(f"  {'─' * len(title)}")

    for i, option in enumerate(options, 1):
        print(f"  {i:3d}. {option}")

    if allow_skip:
        print(f"    0. Saltar / Sin filtro")

    print()

    while True:
        try:
            choice = input("  Selecciona una opción: ").strip()
            if not choice:
                continue
            num = int(choice)
            if allow_skip and num == 0:
                return -1
            if 1 <= num <= len(options):
                return num - 1
            print(f"  ⚠ Introduce un número entre {'0' if allow_skip else '1'} y {len(options)}")
        except ValueError:
            print("  ⚠ Introduce un número válido")


def select_actividad() -> Optional[str]:
    """Menú para seleccionar actividad.

    Returns:
        Slug de la actividad seleccionada, o None si se salta.
    """
    names = list(ACTIVIDADES.keys())
    idx = print_menu("SELECCIONA ACTIVIDAD", names, allow_skip=True)
    if idx == -1:
        return None
    selected = names[idx]
    print(f"  ✓ Actividad: {selected}")
    return ACTIVIDADES[selected]


def select_provincia() -> Optional[str]:
    """Menú para seleccionar provincia.

    Returns:
        Slug de la provincia seleccionada, o None si se salta.
    """
    names = list(PROVINCIAS.keys())
    idx = print_menu("SELECCIONA PROVINCIA", names, allow_skip=True)
    if idx == -1:
        return None
    selected = names[idx]
    print(f"  ✓ Provincia: {selected}")
    return PROVINCIAS[selected]


def select_localidad() -> Optional[str]:
    """Pide al usuario una localidad en formato libre.

    Returns:
        Slug de localidad (ej: "UBEDA-JAEN") o None.
    """
    print("\n  LOCALIDAD (formato: NOMBRE-PROVINCIA)")
    print("  Ejemplos: UBEDA-JAEN, VIGO-PONTEVEDRA, TORRE-CAMPO-JAEN")
    print("  Deja vacío para saltar.\n")

    localidad = input("  Localidad: ").strip().upper()
    if not localidad:
        return None

    # Normalizar: reemplazar espacios por guiones
    localidad = localidad.replace(" ", "-")
    print(f"  ✓ Localidad: {localidad}")
    return localidad


def select_ubicacion() -> tuple[Optional[str], Optional[str]]:
    """Menú para seleccionar tipo de ubicación.

    Returns:
        Tupla (provincia_slug, localidad_slug). Uno será None.
    """
    options = ["Por provincia", "Por localidad", "Sin filtro de ubicación"]
    idx = print_menu("TIPO DE UBICACIÓN", options)

    if idx == 0:
        return select_provincia(), None
    elif idx == 1:
        return None, select_localidad()
    else:
        return None, None


def select_max_results() -> Optional[int]:
    """Pide al usuario el límite de resultados.

    Returns:
        Máximo de resultados, o None para todos.
    """
    print("\n  LÍMITE DE RESULTADOS")
    print("  ─────────────────────")
    print("  Introduce el número máximo de empresas a extraer.")
    print("  Escribe 0 o deja vacío para extraer TODAS.\n")

    while True:
        try:
            value = input("  Máximo de resultados: ").strip()
            if not value or value == "0":
                print("  ✓ Sin límite - se extraerán todas las empresas")
                return None
            num = int(value)
            if num > 0:
                print(f"  ✓ Límite: {num} empresas")
                return num
            print("  ⚠ Introduce un número positivo o 0 para todas")
        except ValueError:
            print("  ⚠ Introduce un número válido")


def confirm_filters(
    actividad_slug: Optional[str],
    provincia_slug: Optional[str],
    localidad_slug: Optional[str],
    max_results: Optional[int],
) -> bool:
    """Muestra resumen de filtros y pide confirmación.

    Returns:
        True si el usuario confirma, False si cancela.
    """
    print(f"\n{'═' * 50}")
    print("  RESUMEN DE BÚSQUEDA")
    print(f"{'═' * 50}")

    # Buscar nombres display
    act_name = "Todas"
    if actividad_slug:
        for name, slug in ACTIVIDADES.items():
            if slug == actividad_slug:
                act_name = name
                break

    prov_name = "Todas"
    if provincia_slug:
        for name, slug in PROVINCIAS.items():
            if slug == provincia_slug:
                prov_name = name
                break

    print(f"  Actividad:   {act_name}")
    if localidad_slug:
        print(f"  Localidad:   {localidad_slug}")
    else:
        print(f"  Provincia:   {prov_name}")
    print(f"  Límite:      {'Sin límite' if not max_results else f'{max_results} empresas'}")
    print(f"{'═' * 50}")

    while True:
        resp = input("\n  ¿Iniciar scraping? (s/n): ").strip().lower()
        if resp in ("s", "si", "sí", "y", "yes", ""):
            return True
        if resp in ("n", "no"):
            return False
        print("  ⚠ Responde 's' o 'n'")


def progress_printer(message: str) -> None:
    """Callback para mostrar progreso en consola."""
    print(message)


def setup_logging():
    """Configura logging a fichero y consola."""
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"output/scraper_{timestamp}.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    # Reducir verbosidad de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return log_file


def main():
    """Punto de entrada principal del CLI."""
    clear_screen()
    print_header()

    # --- Selección de filtros ---
    print("  Configura los filtros de búsqueda:\n")

    # Actividad
    actividad_slug = select_actividad()

    # Ubicación
    provincia_slug, localidad_slug = select_ubicacion()

    # Validar que hay al menos un filtro
    if not any([actividad_slug, provincia_slug, localidad_slug]):
        print("\n  ⚠ Debes seleccionar al menos un filtro (actividad o ubicación).")
        print("  Ejecuta el programa de nuevo.\n")
        input("  Pulsa Enter para salir...")
        return

    # Límite de resultados
    max_results = select_max_results()

    # Confirmación
    if not confirm_filters(actividad_slug, provincia_slug, localidad_slug, max_results):
        print("\n  Operación cancelada.\n")
        return

    # --- Setup ---
    log_file = setup_logging()
    logger = logging.getLogger(__name__)

    # Generar nombre de archivo descriptivo
    parts = []
    if actividad_slug:
        parts.append(actividad_slug.lower())
    if provincia_slug:
        parts.append(provincia_slug.lower())
    if localidad_slug:
        parts.append(localidad_slug.lower())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "_".join(parts) + f"_{timestamp}" if parts else f"empresas_{timestamp}"

    # --- Scraping ---
    scraper = EmpresiteScraper(output_dir="output")

    result = None
    try:
        result = scraper.run(
            actividad_slug=actividad_slug,
            provincia_slug=provincia_slug,
            localidad_slug=localidad_slug,
            max_results=max_results,
            output_filename=filename,
            progress_callback=progress_printer,
        )

        # --- Exportación ---
        if result.empresas_ok:
            json_path, csv_path = export_all(
                result.empresas_ok,
                output_dir="output",
                filename=filename,
            )
            print(f"\n  Archivo JSON: {json_path}")
            print(f"  Archivo CSV:  {csv_path}")

        # Resumen
        print(result.summary())
        print(f"\n  Log detallado: {os.path.abspath(log_file)}")

    except KeyboardInterrupt:
        print("\n\n  ⚠ Scraping interrumpido por el usuario.")
        scraper.close()
        if result and result.empresas_ok:
            json_path, csv_path = export_all(
                result.empresas_ok,
                output_dir="output",
                filename=filename + "_parcial",
            )
            print(f"  Datos parciales guardados:")
            print(f"    JSON: {json_path}")
            print(f"    CSV:  {csv_path}")
    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        scraper.close()
        print(f"\n  ✗ Error: {e}")
        print(f"  Revisa el log: {os.path.abspath(log_file)}")

    print()
    input("  Pulsa Enter para salir...")


if __name__ == "__main__":
    # Asegurar que el directorio raíz del proyecto está en sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    main()
