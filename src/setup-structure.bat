@echo off
chcp 65001 >nul
echo ========================================
echo PY-Indexer v3.0 - Project Structure Setup
echo ========================================
echo.

set BASE_DIR=%~dp0

echo Creating directory structure...
echo.

if not exist "%BASE_DIR%tests" mkdir "%BASE_DIR%tests"
if not exist "%BASE_DIR%builders" mkdir "%BASE_DIR%builders"
if not exist "%BASE_DIR%serializers" mkdir "%BASE_DIR%serializers"
if not exist "%BASE_DIR%viewers" mkdir "%BASE_DIR%viewers"
if not exist "%BASE_DIR%utils" mkdir "%BASE_DIR%utils"
if not exist "%BASE_DIR%cli" mkdir "%BASE_DIR%cli"

echo [OK] Directory structure created
echo.

echo Creating __init__.py files...
type nul > "%BASE_DIR%__init__.py"
type nul > "%BASE_DIR%tests\__init__.py"
type nul > "%BASE_DIR%builders\__init__.py"
type nul > "%BASE_DIR%serializers\__init__.py"
type nul > "%BASE_DIR%viewers\__init__.py"
type nul > "%BASE_DIR%utils\__init__.py"
type nul > "%BASE_DIR%cli\__init__.py"

echo [OK] __init__.py files created
echo.

echo Creating placeholder files...
type nul > "%BASE_DIR%main.py"
type nul > "%BASE_DIR%parser.py"
type nul > "%BASE_DIR%indexer.py"
type nul > "%BASE_DIR%validator.py"
type nul > "%BASE_DIR%requirements.txt"
type nul > "%BASE_DIR%pyproject.toml"
type nul > "%BASE_DIR%main.log"

echo [OK] Placeholder files created
echo.

echo ========================================
echo Structure created successfully!
echo ========================================
echo.
echo Ready for module implementation!
echo.
pause
