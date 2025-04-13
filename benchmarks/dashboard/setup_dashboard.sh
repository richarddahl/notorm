#!/bin/bash
# Simplified setup script for dashboard dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Dashboard Setup Script ==="
echo "This script sets up the Python environment for the dashboard"

# Check Python version
PYTHON_VERSION=$(python3 --version)
echo "Using $PYTHON_VERSION"

# Create a new virtual environment
echo "Creating a fresh virtual environment..."
rm -rf venv
python3 -m venv venv

# Activate the environment
source venv/bin/activate

# Update pip, setuptools and wheel
echo "Updating base packages..."
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dashboard dependencies..."
pip install dash plotly pandas numpy

# Verify installation
echo "Verifying installation..."
python test_install.py

echo -e "\nSetup complete! If all dependencies are installed, you can now run:"
echo "    ./run_dashboard.sh"