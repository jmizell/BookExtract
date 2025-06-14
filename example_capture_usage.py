#!/usr/bin/env python3
"""
Example showing how to use the BookCapture class independently of the GUI.

This demonstrates how the modular design allows the capture functionality
to be used in different contexts (CLI, web interface, etc.).
"""

from book_capture import BookCapture
import time

def progress_callback(current_page, status):
    """Handle progress updates."""
    print(f"Progress: {status}")

def log_callback(message):
    """Handle log messages."""
    print(f"Log: {message}")

def completion_callback(success, message):
    """Handle completion."""
    print(f"Completion: {'Success' if success else 'Failed'} - {message}")

def main():
    """Example usage of BookCapture class."""
    print("BookCapture Class Usage Example")
    print("=" * 40)
    
    # Create capture instance
    capture = BookCapture()
    
    # Set up callbacks
    capture.set_callbacks(
        progress_callback=progress_callback,
        log_callback=log_callback,
        completion_callback=completion_callback
    )
    
    # Check dependencies
    print("\nChecking dependencies...")
    deps_ok, missing = capture.check_dependencies()
    if not deps_ok:
        print(f"Missing dependencies: {missing}")
        print("Please install: sudo apt-get install imagemagick xdotool")
        return
    
    # Example parameters (would normally come from command line or config)
    params = {
        'pages': '3',  # Small number for testing
        'delay': '1.0',
        'save_location': '/tmp/book_capture_test',
        'next_x': '100',
        'next_y': '200',
        'safe_x': '50',
        'safe_y': '150'
    }
    
    # Validate parameters
    print("\nValidating parameters...")
    valid, error = capture.validate_capture_params(params)
    if not valid:
        print(f"Invalid parameters: {error}")
        return
    
    print("Parameters are valid!")
    
    # Test coordinates (optional)
    print("\nTesting coordinates...")
    success, message = capture.test_coordinates(
        int(params['next_x']), int(params['next_y']),
        int(params['safe_x']), int(params['safe_y'])
    )
    
    if success:
        print("Coordinate test successful!")
    else:
        print(f"Coordinate test failed: {message}")
    
    # Note: We don't actually start capture here since it would require
    # a real book viewer to be open. In a real scenario, you would call:
    # capture.start_capture(params)
    
    print("\nExample completed!")
    print("\nTo actually start capture, ensure:")
    print("1. A book viewer is open and visible")
    print("2. The book is on the first page to capture")
    print("3. The coordinates point to the correct UI elements")
    print("4. Then call: capture.start_capture(params)")

if __name__ == "__main__":
    main()