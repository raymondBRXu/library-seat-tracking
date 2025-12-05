#!/bin/bash

# Define environment name
VENV_DIR=".venv"

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found. Please install Python 3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python -m venv $VENV_DIR
else
    echo "Virtual environment already exists in $VENV_DIR."
fi

# Activate virtual environment
source $VENV_DIR/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Installing default dependencies..."
    pip install streamlit ultralytics
fi

echo ""
echo "------------------------------------------------------------------"
echo "Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Activate the environment: source $VENV_DIR/bin/activate"
echo "  2. Run the app: streamlit run GUI/app.py"
echo "------------------------------------------------------------------"