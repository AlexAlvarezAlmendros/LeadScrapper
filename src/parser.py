"""Parseo de HTML de Empresite → datos estructurados."""

import re
import html as html_module
from typing import Optional
from bs4 import BeautifulSoup, Tag

from src.models import Empresa


def parse_listing_page(page_html: str) -> list[str]:
    """Extrae las URLs de fichas de empresa de una página de listado.

    Busca las tarjetas de empresa (.cardCompanyBox) y extrae la URL
    del atributo meta[itemprop="url"].

    Args:
        page_html: HTML completo de la página de listado.

    Returns:
        Lista de URLs absolutas de fichas de empresa.
    """
    soup = BeautifulSoup(page_html, "lxml")
    urls = []

    cards = soup.find_all("div", class_="cardCompanyBox")
    for card in cards:
        # Buscar meta con itemprop="url" dentro de la tarjeta
        meta_url = card.find("meta", attrs={"itemprop": "url"})
        if meta_url and meta_url.get("content"):
            url = str(meta_url["content"])
            if not url.startswith("http"):
                url = f"https://empresite.eleconomista.es{url}"
            urls.append(url)
            continue

        # Fallback: buscar enlace a ficha en el h3
        h3 = card.find("h3")
        if h3:
            link = h3.find("a", href=True)
            if link and str(link["href"]).endswith(".html"):
                href = str(link["href"])
                if not href.startswith("http"):
                    href = f"https://empresite.eleconomista.es{href}"
                urls.append(href)

    return urls


def parse_result_count(page_html: str) -> int:
    """Extrae el número total de resultados del panel de filtros.

    Busca el texto "Hemos encontrado N empresas..." en el elemento
    #filter-numresultados.

    Args:
        page_html: HTML completo de la página de listado.

    Returns:
        Número total de empresas encontradas, 0 si no se puede determinar.
    """
    soup = BeautifulSoup(page_html, "lxml")

    filter_text = soup.find(id="filter-numresultados")
    if filter_text:
        text = filter_text.get_text()
        match = re.search(r"(\d+)\s*empresas?", text)
        if match:
            return int(match.group(1))

    # Fallback: buscar en el texto general
    text = soup.get_text()
    match = re.search(r"Hemos encontrado\s+(\d+)\s+empresas?", text)
    if match:
        return int(match.group(1))

    return 0


def _clean_text(text: Optional[str]) -> str:
    """Limpia texto extraído del HTML."""
    if not text:
        return ""
    # Decodificar HTML entities
    text = html_module.unescape(text)
    # Normalizar espacios
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_placeholder(text: str) -> bool:
    """Detecta si un valor es un placeholder (ej: 'Añadir Teléfono')."""
    placeholders = ["añadir", "agregar", "no disponible", "no consta"]
    return any(p in text.lower() for p in placeholders)


def _extract_field_value(soup: BeautifulSoup, field_label: str) -> str:
    """Extrae el valor de un campo buscando el patrón <h3>Label</h3> + valor.

    En las fichas de Empresite, los datos están estructurados como:
    <h3>Razón social</h3> <p>Valor</p>
    o similar con diferentes tags hermanos.

    Args:
        soup: BeautifulSoup del HTML de la ficha.
        field_label: Texto de la etiqueta a buscar (ej: "Razón social").

    Returns:
        Valor del campo limpio, o cadena vacía si no se encuentra.
    """
    # Buscar h3 que contenga el label
    for h3 in soup.find_all("h3"):
        h3_text = _clean_text(h3.get_text())
        if field_label.lower() in h3_text.lower():
            # El valor suele estar en el siguiente hermano
            sibling = h3.find_next_sibling()
            if sibling:
                value = _clean_text(sibling.get_text())
                if value and not _is_placeholder(value):
                    return value

            # A veces el valor está en el padre como texto posterior
            parent = h3.parent
            if parent:
                # Obtener texto del padre excluyendo el h3
                texts = []
                for child in parent.children:
                    if child != h3 and hasattr(child, "get_text"):
                        texts.append(_clean_text(child.get_text()))
                    elif isinstance(child, str):
                        cleaned = _clean_text(child)
                        if cleaned:
                            texts.append(cleaned)
                value = " ".join(t for t in texts if t and not _is_placeholder(t))
                if value:
                    return value
    return ""


def _extract_field_by_pattern(text: str, pattern: str) -> str:
    """Extrae un valor usando regex sobre el texto completo."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return _clean_text(match.group(1))
    return ""


def parse_company_page(page_html: str, url: str) -> Empresa:
    """Parsea la ficha completa de una empresa.

    Extrae todos los campos disponibles de la página de detalle,
    manejando campos vacíos y placeholders.

    Args:
        page_html: HTML completo de la ficha de empresa.
        url: URL de la ficha (se almacena en el resultado).

    Returns:
        Objeto Empresa con los campos extraídos.
    """
    soup = BeautifulSoup(page_html, "lxml")
    empresa = Empresa(url_ficha=url)

    # --- Información general ---
    empresa.razon_social = _extract_field_value(soup, "Razón social")
    if not empresa.razon_social:
        empresa.razon_social = _extract_field_value(soup, "Razón Social")
    # Fallback: título de la página
    if not empresa.razon_social:
        title = soup.find("title")
        if title:
            title_text = _clean_text(title.get_text())
            # El título suele ser "NOMBRE EMPRESA - Empresite"
            if " - " in title_text:
                empresa.razon_social = title_text.split(" - ")[0].strip()

    empresa.cif = _extract_field_value(soup, "CIF")
    empresa.forma_juridica = _extract_field_value(soup, "Forma jur")
    empresa.sector = _extract_field_value(soup, "Sector")
    empresa.fecha_constitucion = _extract_field_value(soup, "Fecha de constituci")
    empresa.objeto_social = _extract_field_value(soup, "Objeto social")
    empresa.actividad = _extract_field_value(soup, "Actividad CNAE")
    if not empresa.actividad:
        empresa.actividad = _extract_field_value(soup, "Actividad")
    empresa.cnae = _extract_field_value(soup, "CNAE")
    empresa.estado = _extract_field_value(soup, "Estado")

    # --- Dirección y contacto ---
    empresa.direccion = _extract_field_value(soup, "Direcci")
    if not empresa.direccion:
        # Buscar en el schema.org PostalAddress
        addr = soup.find(attrs={"itemprop": "address"})
        if addr:
            empresa.direccion = _clean_text(addr.get_text())

    empresa.telefono = _extract_field_value(soup, "Teléfono")
    if not empresa.telefono:
        empresa.telefono = _extract_field_value(soup, "Tel")

    empresa.email = _extract_field_value(soup, "Email")
    if not empresa.email:
        empresa.email = _extract_field_value(soup, "Correo")

    empresa.web = _extract_field_value(soup, "Web")
    if not empresa.web:
        empresa.web = _extract_field_value(soup, "Página web")
    # Limpiar placeholder de web
    if empresa.web and _is_placeholder(empresa.web):
        empresa.web = ""

    # --- Datos comerciales ---
    empresa.ventas = _extract_field_value(soup, "ventas")
    if not empresa.ventas:
        empresa.ventas = _extract_field_value(soup, "Facturación")
    if not empresa.ventas:
        empresa.ventas = _extract_field_value(soup, "Evolución de ventas")

    empresa.num_empleados = _extract_field_value(soup, "empleados")
    if not empresa.num_empleados:
        empresa.num_empleados = _extract_field_value(soup, "Número de empleados")

    empresa.participaciones = _extract_field_value(soup, "Participaciones")
    empresa.operaciones_internacionales = _extract_field_value(soup, "Operaciones Internacional")
    empresa.grupo_sector = _extract_field_value(soup, "Grupo Sector")
    empresa.cotiza_bolsa = _extract_field_value(soup, "Cotiza")

    return empresa
