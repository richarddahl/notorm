#!/bin/bash

# This script launches the Uno Data Modeler for visual data modeling.

echo "Launching Uno Data Modeler..."
echo ""

# Check if virtual environment is active, activate it if not
if [ -z "$VIRTUAL_ENV" ]; then
  if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
  else
    echo "Warning: No virtual environment found. Dependencies may be missing."
  fi
fi

# Launch the modeler
python -m uno.devtools.cli.main modeler start "$@"