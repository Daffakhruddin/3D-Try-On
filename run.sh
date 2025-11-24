#!/bin/bash
# AR Helmet Try-On System - Quick Run Script
# Run this script to start the application

echo "Starting AR Helmet Try-On System..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment and run
source venv/bin/activate
python src/main.py
