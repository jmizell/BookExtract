#!/usr/bin/env python3
"""
Example script demonstrating how to use the ImageProcessor class independently
from the GUI components.
"""

import sys
import tempfile
from pathlib import Path

# Mock tkinter to avoid display dependencies
import unittest.mock
mock_tk = unittest.mock.MagicMock()
mock_ttk = unittest.mock.MagicMock()
mock_filedialog = unittest.mock.MagicMock()
mock_messagebox = unittest.mock.MagicMock()

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock_ttk
sys.modules['tkinter.filedialog'] = mock_filedialog
sys.modules['tkinter.messagebox'] = mock_messagebox

mock_tk.ttk = mock_ttk
mock_tk.filedialog = mock_filedialog
mock_tk.messagebox = mock_messagebox

# Now import our ImageProcessor
from crop_gui import ImageProcessor


def main():
    """Demonstrate ImageProcessor usage."""
    print("ImageProcessor Example")
    print("=" * 30)
    
    # Create an ImageProcessor instance
    processor = ImageProcessor()
    print("✓ ImageProcessor created")
    
    # Set custom crop coordinates
    processor.set_crop_coordinates(100, 50, 400, 600)
    x, y, w, h = processor.get_crop_coordinates()
    print(f"✓ Crop coordinates set to: x={x}, y={y}, width={w}, height={h}")
    
    # Check dependencies
    if processor.check_dependencies():
        print("✓ Pillow dependency is available")
    else:
        print("✗ Pillow dependency is missing")
        return
    
    # Validate coordinates
    try:
        processor.validate_crop_coordinates()
        print("✓ Crop coordinates are valid")
    except ValueError as e:
        print(f"✗ Invalid crop coordinates: {e}")
        return
    
    # Example of how you could use it with actual images
    print("\nExample usage with image folder:")
    print("processor.load_images_from_folder('/path/to/images')")
    print("processor.process_images('/path/to/output')")
    
    print("\nThe ImageProcessor can now be used independently of the GUI!")


if __name__ == "__main__":
    main()