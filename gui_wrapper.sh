#!/bin/bash
# Setup Report Processor - GUI Launcher (Linux/Mac)
# ==================================================
# This script launches the GUI wrapper for the Setup Report Processor.
# It automatically sets up a virtual environment and installs dependencies on first run.

cd "$(dirname "$0")"

echo "========================================"
echo "Setup Report Processor - GUI"
echo "========================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment..."
    echo "This will only happen once."
    echo

    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        echo "Please ensure Python 3.10+ is installed."
        exit 1
    fi

    source venv/bin/activate

    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install core dependencies."
        exit 1
    fi

    # Try to install GUI dependencies (optional)
    pip install -r requirements-gui.txt
    if [ $? -ne 0 ]; then
        echo "Warning: tkinterdnd2 installation failed."
        echo "Drag-and-drop will use fallback mode (click to browse)."
        echo
    fi

    echo
    echo "Setup complete!"
    echo
else
    source venv/bin/activate
fi

# Launch the GUI
echo "Launching GUI..."
python3 gui_wrapper.py

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: GUI failed to start."
    echo "Check the error messages above for details."
    exit 1
fi
