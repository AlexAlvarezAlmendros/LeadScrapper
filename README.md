# LeadScrapper

Extractor de datos de empresas españolas desde [Empresite (eleconomista.es)](https://empresite.eleconomista.es/). Permite buscar empresas por **actividad**, **provincia** y/o **localidad**, acceder a la ficha completa de cada empresa y exportar los resultados a JSON y CSV.

## Características

- **Filtros combinables**: actividad (22 sectores) + provincia (52) + localidad (texto libre)
- **Extracción completa**: entra en cada ficha de empresa para obtener todos los datos
- **Exportación dual**: JSON y CSV (separador `;` compatible con Excel español)
- **Guardado incremental**: guarda progreso cada 10 empresas para no perder datos
- **Rate limiting inteligente**: delays aleatorios y reintentos con backoff exponencial
- **Anti-bot bypass**: utiliza User-Agent de GPTBot (permitido por el `robots.txt` del sitio)
- **CLI interactivo**: menú en consola para seleccionar filtros fácilmente
- **Arranque con un click**: `run.bat` configura todo automáticamente

## Datos extraídos por empresa

| Campo | Ejemplo |
|---|---|
| Razón social | Construcciones Kirak S.L. |
| CIF | B61023487 |
| Forma jurídica | Sociedad limitada |
| Sector / Actividad | Construcción y actividades inmobiliarias |
| CNAE | 4121 - Construcción de edificios residenciales |
| Objeto social | Actividades de empresa inmobiliaria... |
| Estado | Activa / Cierre de hoja registral |
| Fecha constitución | 1-3-1996 |
| Dirección | Calle ejemplo 1, 08001 Barcelona |
| Teléfono | 93 123 45 67 |
| Email / Web | info@ejemplo.com / www.ejemplo.com |
| Ventas | 1.000.000 € (año 2023) |
| Nº empleados | 25 (año 2023) |
| Participaciones | SÍ / NO |
| Operaciones internacionales | Importa / Exporta |
| Cotiza en bolsa | SÍ / NO |

## Requisitos

- Python 3.10+
- Windows (para `run.bat`) o cualquier SO con terminal

## Instalación rápida

**Opción 1 — Con `run.bat` (Windows):**

Doble click en `run.bat`. Crea el entorno virtual, instala dependencias y lanza el programa automáticamente.

**Opción 2 — Manual:**

```bash
# Crear entorno virtual
python -m venv .venv

# Activar
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python -m src.cli
```

## Uso

Al ejecutar, el programa muestra un menú interactivo:

```
╔══════════════════════════════════════════════════════════╗
║            LEADSCRAPPER - Empresite Scraper              ║
║     Extractor de datos de empresas españolas             ║
╚══════════════════════════════════════════════════════════╝

  1. Selecciona actividad (o salta para todas)
  2. Selecciona ubicación (provincia o localidad)
  3. Define límite de resultados (o 0 para todos)
  4. Confirma y comienza el scraping
```

Los resultados se guardan en la carpeta `output/` en formato JSON y CSV.

### Ejemplo

```
  Actividad:   Construcciones
  Localidad:   IGUALADA-BARCELONA
  Límite:      Sin límite

  → 366 empresas encontradas
  → Datos exportados a output/construcciones_igualada-barcelona_20260212.json
  → Datos exportados a output/construcciones_igualada-barcelona_20260212.csv
```

## Estructura del proyecto

```
LeadScrapper/
├── src/
│   ├── cli.py           # Menú interactivo en consola
│   ├── config.py        # Constantes (provincias, actividades, delays)
│   ├── exporter.py      # Exportación a JSON y CSV
│   ├── models.py        # Dataclasses (Empresa, ScrapeProgress)
│   ├── parser.py        # Parsing HTML (listados y fichas)
│   ├── scraper.py       # Motor de scraping con reintentos
│   └── url_builder.py   # Construcción de URLs con filtros
├── output/              # Resultados exportados
├── run.bat              # Lanzador automático (Windows)
├── requirements.txt     # Dependencias Python
└── README.md
```

## Configuración

Los parámetros se pueden ajustar en [src/config.py](src/config.py):

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `REQUEST_DELAY_MIN` | 5.0 s | Delay mínimo entre peticiones |
| `REQUEST_DELAY_MAX` | 10.0 s | Delay máximo entre peticiones |
| `MAX_RETRIES` | 4 | Reintentos ante errores HTTP |
| `RETRY_BACKOFF_BASE` | 30 s | Espera base para backoff exponencial |
| `SAVE_EVERY_N` | 10 | Guardado incremental cada N empresas |

## Licencia

Este proyecto está bajo la licencia [GNU GPL v3](LICENSE).