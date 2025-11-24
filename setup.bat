@echo off
REM AR Helmet Try-On System - Windows Setup Script
REM Run this script to automatically set up the project

echo ============================================================
echo AR Helmet Try-On System - Automatic Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment and install dependencies
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Check for helmet model
echo [4/5] Checking for helmet model...
if exist assets\helmet.glb (
    echo Helmet model found: assets\helmet.glb
) else (
    echo WARNING: Helmet model not found!
    echo Please download a GLB model and place it as: assets\helmet.glb
    echo See assets\README.md for instructions
)
echo.

REM Run system test
echo [5/5] Running system test...
python test_system.py
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo To run the application:
echo   1. Activate virtual environment: venv\Scripts\activate.bat
echo   2. Run: python src\main.py
echo.
echo Or simply run: run.bat
echo.
pause
