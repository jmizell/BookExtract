#!/usr/bin/env python3
"""
Test script to verify the GUI loads without errors.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test import without creating GUI
    import capture_gui
    print("✓ Successfully imported capture_gui module")
    
    # Test that all required modules are available
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    import subprocess
    import threading
    import time
    import os
    from pathlib import Path
    print("✓ All required modules are available")
    
    # Test that the class can be imported
    from capture_gui import CaptureGUI
    print("✓ CaptureGUI class imported successfully")
    
    print("\nModule structure test passed! The GUI should work correctly when run with a display.")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)