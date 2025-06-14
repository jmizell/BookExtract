# Modular Capture Architecture

## Overview

The book capture functionality has been refactored into a modular design that separates the core capture logic from the GUI interface. This makes the code more maintainable, testable, and reusable.

## Architecture

### BookCapture Class (`book_capture.py`)

The `BookCapture` class handles all capture-related functionality:

- **Dependency checking**: Validates that required system tools (ImageMagick, xdotool) are available
- **Parameter validation**: Ensures capture parameters are valid before starting
- **Coordinate testing**: Tests mouse coordinates by moving to specified positions
- **Screenshot capture**: Takes screenshots and navigates between pages
- **Progress tracking**: Provides callbacks for progress updates and logging
- **Error handling**: Comprehensive error handling with detailed messages

#### Key Methods:

- `check_dependencies()`: Returns availability status of required tools
- `validate_capture_params(params)`: Validates capture parameters
- `test_coordinates(x1, y1, x2, y2)`: Tests mouse coordinate positions
- `start_capture(params)`: Starts the capture process
- `cancel_capture()`: Cancels ongoing capture
- `set_callbacks()`: Sets callback functions for progress/logging

#### Callback System:

The class uses a callback system to communicate with the UI:
- `progress_callback(current, status)`: Called for progress updates
- `log_callback(message)`: Called for log messages
- `completion_callback(success, message)`: Called when capture completes

### CaptureGUI Class (`capture_gui.py`)

The `CaptureGUI` class focuses solely on the user interface:

- **UI setup and layout**: Creates and manages all GUI components
- **User input handling**: Manages form inputs and validation
- **Progress display**: Shows progress bars and status updates
- **Event handling**: Handles button clicks, menu actions, etc.
- **Thread management**: Manages capture thread for non-blocking UI

#### Key Changes:

- Removed all capture logic and moved to `BookCapture`
- Uses composition to include a `BookCapture` instance
- Implements callback methods to receive updates from capture handler
- Simplified methods focus only on UI concerns

## Benefits

### 1. Separation of Concerns
- GUI code handles only interface logic
- Capture code handles only capture functionality
- Clear boundaries between components

### 2. Reusability
- `BookCapture` can be used in different contexts (CLI, web interface, etc.)
- See `example_capture_usage.py` for standalone usage

### 3. Testability
- Capture logic can be tested independently
- GUI components can be tested separately
- Easier to mock dependencies for testing

### 4. Maintainability
- Changes to capture logic don't affect GUI
- Changes to GUI don't affect capture logic
- Easier to debug and extend

## Usage Examples

### GUI Usage (existing)
```python
# Run the GUI application
python3 capture_gui.py
```

### Programmatic Usage
```python
from book_capture import BookCapture

# Create capture instance
capture = BookCapture()

# Set up callbacks
capture.set_callbacks(
    progress_callback=my_progress_handler,
    log_callback=my_log_handler,
    completion_callback=my_completion_handler
)

# Configure parameters
params = {
    'pages': '100',
    'delay': '0.5',
    'save_location': '/path/to/save',
    'next_x': '1865',
    'next_y': '650',
    'safe_x': '30',
    'safe_y': '650'
}

# Start capture
if capture.start_capture(params):
    print("Capture started successfully")
```

## Files

- `book_capture.py`: Core capture functionality
- `capture_gui.py`: GUI interface (refactored)
- `example_capture_usage.py`: Example of standalone usage
- `MODULAR_CAPTURE.md`: This documentation

## Migration Notes

The refactoring maintains full backward compatibility for GUI users. The interface and functionality remain exactly the same, but the underlying architecture is now more modular and extensible.