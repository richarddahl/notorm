#!/bin/bash
# Dashboard launcher script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create a Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install setuptools with wheel first to handle distutils issue in Python 3.12+
echo "Installing setuptools and wheel..."
pip install --upgrade pip setuptools wheel

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found, installing essential packages..."
    pip install dash==2.9.3 plotly==5.14.1 pandas==2.0.0 numpy==1.24.3
fi

# Create required directories
mkdir -p data/summaries
mkdir -p assets

# Process benchmark results
echo "Processing benchmark results..."
python process_results.py --sample

# Start the dashboard
echo "Starting dashboard at http://127.0.0.1:8050/ ..."
python app.py