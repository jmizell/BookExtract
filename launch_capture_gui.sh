#!/bin/bash

# Book Page Capture GUI Launcher
# This script launches the GUI version of the capture tool

# Check if we're in the right directory
if [ ! -f "capture_gui.py" ]; then
    echo "Error: capture_gui.py not found in current directory"
    echo "Please run this script from the BookExtract directory"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if tkinter is available
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Error: tkinter is not available"
    echo "Please install tkinter: sudo apt-get install python3-tk"
    exit 1
fi

echo "Launching Book Page Capture GUI..."
python3 capture_gui.py