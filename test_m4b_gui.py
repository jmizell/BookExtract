#!/usr/bin/env python3
"""
Test script for M4B GUI to verify it can be imported and initialized.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gui_import():
    """Test that the GUI module can be imported."""
    try:
        from m4b_gui import M4bGeneratorGUI
        print("✓ M4B GUI module imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import M4B GUI module: {e}")
        return False

def test_gui_class():
    """Test that the GUI class can be instantiated (without actually showing the window)."""
    try:
        import tkinter as tk
        from m4b_gui import M4bGeneratorGUI
        
        # Create root window but don't show it
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Try to create the GUI
        app = M4bGeneratorGUI(root)
        print("✓ M4B GUI class instantiated successfully")
        
        # Test some basic functionality
        if hasattr(app, 'log_message'):
            app.log_message("Test message")
            print("✓ Log message functionality works")
        
        if hasattr(app, 'check_dependencies'):
            print("✓ Dependency checking method available")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Failed to instantiate M4B GUI class: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing M4B GUI...")
    print("=" * 40)
    
    tests = [
        test_gui_import,
        test_gui_class
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! M4B GUI is ready to use.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)