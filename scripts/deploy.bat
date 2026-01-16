@echo off
REM Deployment Helper Script for Windows
REM Usage: deploy.bat [hf|vercel|check]

if "%1"=="" (
    echo Usage: deploy.bat [hf^|vercel^|check]
    echo.
    echo Commands:
    echo   hf      - Deploy to Hugging Face Spaces
    echo   vercel  - Deploy to Vercel
    echo   check   - Check environment configuration
    exit /b 1
)

if "%1"=="check" (
    python scripts/deploy.py check
    exit /b
)

if "%1"=="hf" (
    if "%HF_SPACE_NAME%"=="" (
        echo Error: HF_SPACE_NAME environment variable not set
        echo Set it to your space name, e.g., username/blood-report-analyzer
        exit /b 1
    )
    python scripts/deploy.py hf --space %HF_SPACE_NAME%
    exit /b
)

if "%1"=="vercel" (
    python scripts/deploy.py vercel
    exit /b
)

echo Unknown command: %1
echo Use: hf, vercel, or check
