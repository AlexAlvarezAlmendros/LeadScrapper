@echo off
chcp 65001 >nul
title LeadScrapper - Empresite Scraper

echo.
echo ========================================
echo   LeadScrapper - Empresite Scraper
echo ========================================
echo.

:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Instala Python 3.10+ desde python.org
    echo.
    pause
    exit /b 1
)

:: Verificar/crear entorno virtual
if not exist ".venv" (
    echo [INFO] Creando entorno virtual...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

:: Activar entorno virtual
call .venv\Scripts\activate.bat

:: Instalar dependencias
echo [INFO] Verificando dependencias...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] No se pudieron instalar las dependencias.
    pause
    exit /b 1
)

:: Crear directorio de salida
if not exist "output" mkdir output

:: Ejecutar scraper
echo.
python -m src.cli

:: Desactivar entorno
call deactivate

pause
