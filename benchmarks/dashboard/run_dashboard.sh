#!/bin/bash
# Dashboard launcher script

# Create a Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create data directory
mkdir -p data/summaries

# Process benchmark results
echo "Processing benchmark results..."
python process_results.py

# Start the dashboard
echo "Starting dashboard at http://127.0.0.1:8050/ ..."
python app.py