@echo off
chcp 65001 >nul
echo ========================================
echo PY-Indexer v3.0 - CODE-GUARD Full Index
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

REM Step 1: Generate TECH-INDEX (compact format)
echo ========================================
echo Step 1: Generating TECH-INDEX (compact)
echo ========================================
echo.
python main.py index "%PROJECT_PATH%" "%OUTPUT_PATH%" --format=json --hash-len=16

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: TECH-INDEX generation failed!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo SUCCESS: TECH-INDEX generated!
echo   File: %OUTPUT_PATH%\tech-index.json
echo.

REM Step 2: Generate TECH-LOCATION (human-readable format)
echo ========================================
echo Step 2: Generating TECH-LOCATION (readable)
echo ========================================
echo.
python main.py location "%OUTPUT_PATH%" "%OUTPUT_PATH%\tech-index.json"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: TECH-LOCATION generation failed!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo SUCCESS: TECH-LOCATION generated!
echo   File: %OUTPUT_PATH%\tech-location.json
echo.

REM Display file sizes
echo ========================================
echo Generated Files:
echo ========================================
for %%F in ("%OUTPUT_PATH%\tech-index.json") do (
    echo   TECH-INDEX:    %%~zF bytes ^(%%~nxF^)
)
for %%F in ("%OUTPUT_PATH%\tech-location.json") do (
    echo   TECH-LOCATION: %%~zF bytes ^(%%~nxF^)
)
echo.

REM Show quick stats
echo ========================================
echo Quick View:
echo ========================================
python main.py view "%OUTPUT_PATH%\tech-location.json" --no-stats

echo.
echo ========================================
echo COMPLETE! Both indexes generated.
echo.
echo Next Steps:
echo   1. View full index:
echo      python main.py view "%OUTPUT_PATH%\tech-location.json"
echo.
echo   2. Filter by type:
echo      python main.py view "%OUTPUT_PATH%\tech-location.json" --filter=functions
echo.
echo   3. Use TECH-INDEX for AI analysis:
echo      Feed %OUTPUT_PATH%\tech-index.json to LLM
echo.
echo   4. Use TECH-LOCATION for human reading:
echo      Open %OUTPUT_PATH%\tech-location.json
echo ========================================
echo.
pause
