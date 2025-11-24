#!/bin/bash
# AR Helmet Try-On System - Linux/Mac Setup Script
# Run this script to automatically set up the project

set -e

echo "============================================================"
echo "AR Helmet Try-On System - Automatic Setup"
echo "============================================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10+ from your package manager"
    exit 1
fi

echo "[1/5] Python found:"
python3 --version
echo

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "Virtual environment created successfully"
fi
echo

# Activate virtual environment and install dependencies
echo "[3/5] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt
echo "Dependencies installed successfully"
echo

# Check for helmet model
echo "[4/5] Checking for helmet model..."
if [ -f "assets/helmet.glb" ]; then
    echo "Helmet model found: assets/helmet.glb"
else
    echo "WARNING: Helmet model not found!"
    echo "Please download a GLB model and place it as: assets/helmet.glb"
    echo "See assets/README.md for instructions"
fi
echo

# Run system test
echo "[5/5] Running system test..."
python test_system.py
echo

echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo
echo "To run the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: python src/main.py"
echo
echo "Or simply run: ./run.sh"
echo
