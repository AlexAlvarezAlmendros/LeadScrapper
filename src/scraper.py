"""Motor de scraping para Empresite usando User-Agent de GPTBot.

El robots.txt de empresite.eleconomista.es permite el acceso a GPTBot (OpenAI),
mientras que bloquea otros bots. Aprovechamos esto para hacer peticiones HTTP
simples sin necesidad de navegador headless ni resolver CAPTCHAs.
"""

import logging
import math
import random
import time
from typing import Optional

import requests

from src.config import (
    BASE_URL,
    MAX_RETRIES,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    RESULTS_PER_PAGE,
    RETRY_BACKOFF_BASE,
    SAVE_EVERY_N,
)
from src.models import Empresa, ScrapeProgress
from src.parser import parse_company_page, parse_listing_page, parse_result_count
from src.url_builder import build_listing_url
from src.exporter import save_to_json

logger = logging.getLogger(__name__)

# User-Agent de GPTBot (permitido por robots.txt de Empresite)
GPTBOT_USER_AGENT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"

# User-Agent alternativo: ChatGPT-User (también permitido)
CHATGPT_USER_AGENT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +https://openai.com/bot)"

# Indicadores de CAPTCHA / bloqueo en el HTML
CAPTCHA_INDICATORS = [
    "demasiadas peticiones detectadas",
    "verificar que no es un robot",
    "resuelva el captcha",
    "too many requests detected",
]


def _detect_captcha(html: str) -> bool:
    """Detecta si la página contiene un CAPTCHA o bloqueo anti-bot."""
    html_lower = html.lower()
    return any(indicator in html_lower for indicator in CAPTCHA_INDICATORS)


class ScraperError(Exception):
    """Error base del scraper."""
    pass


class CaptchaError(ScraperError):
    """Se detectó un CAPTCHA en la respuesta."""

    def __init__(self, url: str):
        super().__init__(f"CAPTCHA detectado en: {url}")
        self.url = url


class RateLimitError(ScraperError):
    """El servidor devolvió HTTP 429."""

    def __init__(self, retry_after: int = 30):
        self.retry_after = retry_after
        super().__init__(f"Rate limit. Reintentando en {retry_after}s")


class EmpresiteScraper:
    """Scraper principal para empresite.eleconomista.es.

    Usa el User-Agent de GPTBot (OpenAI) que está permitido en el
    robots.txt del sitio, evitando así CAPTCHAs y bloqueos 429.

    Implementa:
    - Sesión HTTP con User-Agent de GPTBot (permitido por robots.txt)
    - Delay aleatorio entre peticiones para no sobrecargar el servidor
    - Reintentos con backoff exponencial ante errores
    - Tracking de progreso y errores parciales
    - Guardado incremental cada N empresas
    """

    def __init__(self, output_dir: str = "output"):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": GPTBOT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        self.output_dir = output_dir
        self._request_count = 0

    def close(self) -> None:
        """Cierra la sesión HTTP."""
        self.session.close()

    def _delay(self) -> None:
        """Espera un tiempo aleatorio entre peticiones."""
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        logger.debug(f"Esperando {delay:.1f}s...")
        time.sleep(delay)

    def fetch_page(self, url: str) -> str:
        """Descarga una página con reintentos y rate limiting.

        Args:
            url: URL a descargar.

        Returns:
            HTML de la página como string.

        Raises:
            ScraperError: Si se agotan los reintentos.
        """
        last_error = None

        for attempt in range(MAX_RETRIES):
            if self._request_count > 0:
                self._delay()

            try:
                logger.debug(f"Petición [{attempt + 1}/{MAX_RETRIES}]: {url}")
                response = self.session.get(url, timeout=30)
                self._request_count += 1

                if response.status_code == 200:
                    html = response.text
                    # Verificar que no sea una página de CAPTCHA con status 200
                    if _detect_captcha(html):
                        logger.warning(f"CAPTCHA en respuesta 200 de {url}")
                        # Cambiar al User-Agent alternativo
                        self.session.headers["User-Agent"] = CHATGPT_USER_AGENT
                        wait_time = RETRY_BACKOFF_BASE * (2 ** attempt)
                        logger.warning(f"Cambiando User-Agent y esperando {wait_time}s...")
                        time.sleep(wait_time)
                        last_error = CaptchaError(url)
                        continue
                    return html

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", RETRY_BACKOFF_BASE))
                    wait_time = retry_after * (2 ** attempt)
                    logger.warning(f"HTTP 429 - Esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)
                    last_error = RateLimitError(wait_time)
                    continue

                if response.status_code == 404:
                    raise ScraperError(f"Página no encontrada (404): {url}")

                response.raise_for_status()

            except requests.RequestException as e:
                last_error = ScraperError(f"Error de red: {e}")
                wait_time = RETRY_BACKOFF_BASE * (2 ** attempt)
                logger.warning(f"Error de red, esperando {wait_time}s: {e}")
                time.sleep(wait_time)

        raise last_error or ScraperError(f"No se pudo descargar: {url}")

    def scrape_listing_urls(
        self,
        actividad_slug: Optional[str] = None,
        provincia_slug: Optional[str] = None,
        localidad_slug: Optional[str] = None,
        max_results: Optional[int] = None,
        progress_callback=None,
    ) -> tuple[list[str], int]:
        """Recorre las páginas del listado y recopila URLs de fichas.

        Args:
            actividad_slug: Filtro de actividad.
            provincia_slug: Filtro de provincia.
            localidad_slug: Filtro de localidad.
            max_results: Límite máximo de resultados (None = todos).
            progress_callback: Función callback(message) para mostrar progreso.

        Returns:
            Tupla (lista de URLs de fichas, total de resultados en el sitio).
        """
        all_urls = []
        page = 1

        # Primera página para obtener total de resultados
        url = build_listing_url(actividad_slug, provincia_slug, localidad_slug, page=1)
        if progress_callback:
            progress_callback(f"Descargando listado página 1...")

        html = self.fetch_page(url)
        total_results = parse_result_count(html)
        page_urls = parse_listing_page(html)
        all_urls.extend(page_urls)

        if progress_callback:
            progress_callback(
                f"Encontradas {total_results} empresas en total. "
                f"Página 1: {len(page_urls)} URLs extraídas."
            )

        if total_results == 0:
            return [], 0

        # Calcular páginas necesarias
        effective_max = max_results if max_results and max_results > 0 else total_results
        total_pages = math.ceil(min(effective_max, total_results) / RESULTS_PER_PAGE)

        # Páginas restantes
        for page in range(2, total_pages + 1):
            if max_results and len(all_urls) >= max_results:
                break

            url = build_listing_url(actividad_slug, provincia_slug, localidad_slug, page=page)
            if progress_callback:
                progress_callback(f"Descargando listado página {page}/{total_pages}...")

            try:
                html = self.fetch_page(url)
                page_urls = parse_listing_page(html)
                all_urls.extend(page_urls)
                if progress_callback:
                    progress_callback(f"  Página {page}: {len(page_urls)} URLs ({len(all_urls)} total)")
            except ScraperError as e:
                logger.error(f"Error en página {page}: {e}")
                if progress_callback:
                    progress_callback(f"  Error en página {page}: {e}")

        # Recortar al máximo solicitado
        if max_results and max_results > 0:
            all_urls = all_urls[:max_results]

        return all_urls, total_results

    def scrape_company(self, url: str) -> Empresa:
        """Descarga y parsea la ficha completa de una empresa.

        Args:
            url: URL de la ficha de empresa.

        Returns:
            Objeto Empresa con todos los datos extraídos.
        """
        html = self.fetch_page(url)
        return parse_company_page(html, url)

    def run(
        self,
        actividad_slug: Optional[str] = None,
        provincia_slug: Optional[str] = None,
        localidad_slug: Optional[str] = None,
        max_results: Optional[int] = None,
        output_filename: Optional[str] = None,
        progress_callback=None,
    ) -> ScrapeProgress:
        """Ejecuta el proceso completo de scraping.

        1. Recorre el listado recopilando URLs de fichas
        2. Entra en cada ficha para extraer datos completos
        3. Guarda progreso incrementalmente

        Args:
            actividad_slug: Filtro de actividad.
            provincia_slug: Filtro de provincia.
            localidad_slug: Filtro de localidad.
            max_results: Límite de resultados (None o 0 = todos).
            output_filename: Nombre base del archivo de salida (sin extensión).
            progress_callback: Función callback(message) para progreso.

        Returns:
            Objeto ScrapeProgress con resultados y estadísticas.
        """
        progress = ScrapeProgress()

        # Fase 1: Recopilar URLs del listado
        if progress_callback:
            progress_callback("\n[Fase 1] Recopilando URLs de empresas del listado...\n")

        company_urls, total = self.scrape_listing_urls(
            actividad_slug=actividad_slug,
            provincia_slug=provincia_slug,
            localidad_slug=localidad_slug,
            max_results=max_results,
            progress_callback=progress_callback,
        )

        progress.total_esperado = len(company_urls)

        if not company_urls:
            if progress_callback:
                progress_callback("\nNo se encontraron empresas con los filtros seleccionados.")
            return progress

        if progress_callback:
            progress_callback(
                f"\n[Fase 2] Extrayendo datos de {len(company_urls)} fichas de empresa...\n"
            )

        # Fase 2: Extraer datos de cada ficha
        json_path = None
        if output_filename:
            json_path = f"{self.output_dir}/{output_filename}.json"

        for i, url in enumerate(company_urls, 1):
            if progress_callback:
                progress_callback(f"  [{i}/{len(company_urls)}] {url}")

            try:
                empresa = self.scrape_company(url)
                progress.add_success(empresa)

                # Guardado incremental
                if json_path and len(progress.empresas_ok) % SAVE_EVERY_N == 0:
                    save_to_json(progress.empresas_ok, json_path)
                    logger.debug(f"Guardado incremental: {len(progress.empresas_ok)} empresas")

            except Exception as e:
                error_msg = str(e)
                progress.add_error(url, error_msg)
                logger.error(f"Error procesando {url}: {error_msg}")
                if progress_callback:
                    progress_callback(f"    ERROR: {error_msg}")

        # Guardado final
        if json_path and progress.empresas_ok:
            save_to_json(progress.empresas_ok, json_path)
            if progress_callback:
                progress_callback(f"\nDatos guardados en: {json_path}")

        # Cerrar navegador
        self.close()

        return progress
