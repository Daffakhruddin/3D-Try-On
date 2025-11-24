@echo off
REM AR Helmet Try-On System - Quick Run Script
REM Run this script to start the application

echo Starting AR Helmet Try-On System...
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment and run
call venv\Scripts\activate.bat
python src\main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with error code: %errorlevel%
    pause
)
