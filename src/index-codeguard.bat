@echo off
chcp 65001 >nul
echo ========================================
echo PY-Indexer v3.0 - CODE-GUARD Indexing
echo ========================================
echo.

set PROJECT_PATH=D:\AI-CodeGuard\repo\CODE-GUARD\backend
set OUTPUT_PATH=D:\AI-CodeGuard\repo\CODE-GUARD\Index

echo Project: %PROJECT_PATH%
echo Output:  %OUTPUT_PATH%
echo.

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_PATH%" (
    echo Creating output directory...
    mkdir "%OUTPUT_PATH%"
    echo.
)

REM Run indexing
echo Starting indexing...
echo.
python main.py index "%PROJECT_PATH%" "%OUTPUT_PATH%" --format=json --hash-len=16

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: Indexing completed!
    echo.
    echo Generated files:
    echo   - %OUTPUT_PATH%\tech-index.json
    echo.
    echo To generate TECH-LOCATION, run:
    echo   python main.py location "%OUTPUT_PATH%" "%OUTPUT_PATH%\tech-index.json"
    echo.
    echo To view index:
    echo   python main.py view "%OUTPUT_PATH%\tech-index.json"
) else (
    echo FAILED: Indexing failed with error code %ERRORLEVEL%
)
echo ========================================
echo.
pause
