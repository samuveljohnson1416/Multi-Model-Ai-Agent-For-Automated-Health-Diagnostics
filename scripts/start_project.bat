@echo off
echo 🩺 Blood Report Analysis System - Windows Launcher
echo ================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python first.
    pause
    exit /b 1
)

REM Launch the project
python start_project.py

pause