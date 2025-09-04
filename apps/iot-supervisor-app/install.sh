#!/bin/bash
# IoT Supervisor App Installation Script
set -e

echo "Setting up IoT Supervisor App..."

# Detect current shell
if [ -n "$FISH_VERSION" ]; then
    SHELL_TYPE="fish"
    ACTIVATE_CMD="source .venv/bin/activate.fish"
else
    SHELL_TYPE="bash"
    ACTIVATE_CMD="source .venv/bin/activate"
fi

echo "Detected shell: $SHELL_TYPE"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing bms-schemas package..."
pip install -e ../../packages/bms-schemas

echo "Installing iot-supervisor-app..."
pip install -e .

echo "Installation complete!"
echo "To activate: $ACTIVATE_CMD"
echo "To test: iot-supervisor-app --help"
