"""Configuración y constantes del scraper de Empresite."""

BASE_URL = "https://empresite.eleconomista.es"

# Delay entre peticiones (segundos) - rango aleatorio para evitar detección
REQUEST_DELAY_MIN = 5.0
REQUEST_DELAY_MAX = 10.0

# Reintentos ante errores HTTP
MAX_RETRIES = 4
RETRY_BACKOFF_BASE = 30  # segundos base para backoff exponencial ante 429

# Resultados por página en Empresite
RESULTS_PER_PAGE = 30

# Guardado incremental cada N empresas
SAVE_EVERY_N = 10

# User agents para rotación
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
]

# Provincias: nombre display → slug URL
PROVINCIAS = {
    "Álava": "ALAVA",
    "Albacete": "ALBACETE",
    "Alicante": "ALICANTE",
    "Almería": "ALMERIA",
    "Asturias": "ASTURIAS",
    "Ávila": "AVILA",
    "Badajoz": "BADAJOZ",
    "Baleares": "BALEARES",
    "Barcelona": "BARCELONA",
    "Burgos": "BURGOS",
    "Cáceres": "CACERES",
    "Cádiz": "CADIZ",
    "Cantabria": "CANTABRIA",
    "Castellón": "CASTELLON",
    "Ceuta": "CEUTA",
    "Ciudad Real": "CIUDAD-REAL",
    "Córdoba": "CORDOBA",
    "Coruña": "CORUNA",
    "Cuenca": "CUENCA",
    "Gerona": "GERONA",
    "Granada": "GRANADA",
    "Guadalajara": "GUADALAJARA",
    "Guipúzcoa": "GUIPUZCOA",
    "Huelva": "HUELVA",
    "Huesca": "HUESCA",
    "Jaén": "JAEN",
    "León": "LEON",
    "Lérida": "LERIDA",
    "Lugo": "LUGO",
    "Madrid": "MADRID",
    "Málaga": "MALAGA",
    "Melilla": "MELILLA",
    "Murcia": "MURCIA",
    "Navarra": "NAVARRA",
    "Orense": "ORENSE",
    "Palencia": "PALENCIA",
    "Palmas (Las)": "PALMAS-LAS",
    "Pontevedra": "PONTEVEDRA",
    "Rioja (La)": "RIOJA-LA",
    "Salamanca": "SALAMANCA",
    "Santa Cruz de Tenerife": "SANTA-CRUZ-TENERIFE",
    "Segovia": "SEGOVIA",
    "Sevilla": "SEVILLA",
    "Soria": "SORIA",
    "Tarragona": "TARRAGONA",
    "Teruel": "TERUEL",
    "Toledo": "TOLEDO",
    "Valencia": "VALENCIA",
    "Valladolid": "VALLADOLID",
    "Vizcaya": "VIZCAYA",
    "Zamora": "ZAMORA",
    "Zaragoza": "ZARAGOZA",
}

# Actividades: nombre display → slug URL
ACTIVIDADES = {
    "Agricultura": "AGRICULTURA",
    "Alimentación": "ALIMENTACION",
    "Banca": "BANCA",
    "Construcciones": "CONSTRUCCIONES",
    "Educación": "EDUCACION",
    "Energéticas": "ENERGETICAS",
    "Farmacéutica": "FARMACEUTICA",
    "Ganadería": "GANADERIA",
    "Hostelería": "HOSTELERIA",
    "Inmobiliaria": "INMOBILIARIA",
    "Logística": "LOGISTICA",
    "Manufactura": "MANUFACTURA",
    "Minería": "MINERIA",
    "Ocio": "OCIO",
    "Pesca": "PESCA",
    "Restauración": "RESTAURACION",
    "Sanidad": "SANIDAD",
    "Seguro": "SEGURO",
    "Silvicultura": "SILVICULTURA",
    "Telecomunicaciones": "TELECOMUNICACIONES",
    "Transporte": "TRANSPORTE",
    "Vehículos": "VEHICULOS",
}
