# Book Page Capture GUI

A user-friendly tkinter interface for the automated book page capture functionality, replacing the command-line `capture.sh` script.

## Features

- **Intuitive GUI**: Easy-to-use interface with clear controls and real-time feedback
- **Configurable Settings**: 
  - Number of pages to capture
  - Delay between captures (in seconds)
  - Custom save location with directory browser
  - Adjustable mouse coordinates for navigation buttons
- **Progress Tracking**: Real-time progress bar and status updates
- **Error Handling**: Comprehensive validation and error reporting
- **Cancellation Support**: Ability to stop capture process at any time
- **Status Logging**: Detailed log of capture progress and any issues

## Requirements

- Python 3.6+ with tkinter (usually included)
- ImageMagick (`import` command)
- xdotool (for mouse automation)
- X11 display server (Linux)

### Installation of Dependencies

On Ubuntu/Debian systems:
```bash
sudo apt-get install imagemagick xdotool
```

## Usage

1. **Launch the GUI**:
   ```bash
   python3 capture_gui.py
   ```

2. **Configure Settings**:
   - **Number of pages**: Set how many screenshots to take (default: 380)
   - **Delay**: Time to wait between captures in seconds (default: 0.5)
   - **Save location**: Directory where screenshots will be saved (default: ./images)
   - **Mouse coordinates**: Adjust if your book viewer has different button positions

3. **Mouse Coordinate Setup**:
   - **Next button X/Y**: Coordinates of the "next page" button in your book viewer
   - **Safe area X/Y**: Coordinates of a safe area to click (away from UI elements)
   - Default values work for many common book viewers at 1920x1080 resolution

4. **Start Capture**:
   - Click "Start Capture" to begin the automated process
   - The application will take screenshots and automatically navigate pages
   - Monitor progress through the progress bar and status log
   - Use "Cancel" to stop the process at any time

## How It Works

The GUI replicates the functionality of the original `capture.sh` script:

1. Takes a screenshot of the current screen using ImageMagick's `import` command
2. Moves the mouse to the "next page" button coordinates and clicks
3. Moves the mouse to a safe area and clicks (to ensure focus)
4. Waits for the specified delay
5. Repeats for the specified number of pages

Screenshots are saved as `page000.png`, `page001.png`, etc. in the specified directory.

## Tips for Best Results

1. **Setup your book viewer first**:
   - Open your book/document in full-screen mode
   - Navigate to the first page you want to capture
   - Note the position of the "next page" button

2. **Test coordinates**:
   - Start with a small number of pages (e.g., 5) to test
   - Adjust mouse coordinates if clicks aren't hitting the right buttons
   - The safe area should be somewhere that won't trigger unwanted actions

3. **Optimal settings**:
   - Use 0.5-1.0 second delay for most books
   - Increase delay if pages load slowly
   - Ensure your book viewer doesn't have auto-advance features enabled

## Troubleshooting

### Common Issues

1. **"Missing Dependencies" error**:
   - Install ImageMagick and xdotool as shown above
   - Verify installation with: `import --version` and `xdotool --version`

2. **Screenshots are blank or wrong**:
   - Ensure the book viewer window is visible and not minimized
   - Check that no other windows are covering the book

3. **Navigation not working**:
   - Verify mouse coordinates are correct for your book viewer
   - Test manually clicking at those coordinates
   - Some viewers may require different click patterns

4. **Permission errors**:
   - Ensure the save directory is writable
   - Check that you have permissions to create files in the target location

### Getting Mouse Coordinates

To find the correct coordinates for your book viewer:

1. Open your book viewer
2. Use a tool like `xev` or simply hover over buttons and note coordinates
3. Or use: `xdotool getmouselocation` after positioning your mouse

## Comparison with Original Script

| Feature | capture.sh | capture_gui.py |
|---------|------------|----------------|
| Interface | Command line | Graphical |
| Configuration | Edit script | GUI controls |
| Progress tracking | None | Real-time progress bar |
| Error handling | Basic | Comprehensive |
| Cancellation | Ctrl+C only | Cancel button |
| Validation | None | Input validation |
| Logging | None | Status log |
| Coordinates | Hard-coded | Configurable |

## Next Steps

After capturing pages with this GUI, continue with the rest of the BookExtract pipeline:

1. **Crop images**: `bash crop.sh`
2. **OCR processing**: `bash ocr.sh`
3. **AI enhancement**: `python ocr.py`
4. **Merge content**: `python merge.py`
5. **Generate EPUB**: `python render.py`

## Contributing

This GUI is part of the BookExtract project. Feel free to submit issues or improvements to make the tool even more user-friendly.