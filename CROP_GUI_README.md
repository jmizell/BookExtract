# Crop GUI Tool

A graphical user interface for batch image cropping, based on the functionality of `crop.sh`.

## Features

- **Input/Output Folder Selection**: Choose source and destination folders for your images
- **Image Preview**: View images with navigation controls to browse through your collection
- **Interactive Crop Selection**: Click and drag on the preview to select crop area with your mouse
- **Manual Coordinate Adjustment**: Fine-tune crop boundaries using text input fields
- **Batch Processing**: Process multiple images with the same crop settings
- **Progress Tracking**: Real-time progress bar and status updates
- **No External Dependencies**: Uses Pillow for image processing (no ImageMagick required)

## Requirements

- Python 3.6+
- Pillow (PIL)
- tkinter (usually included with Python)

## Installation

```bash
pip install Pillow
```

## Usage

1. **Run the application**:
   ```bash
   python3 crop_gui.py
   ```

2. **Select folders**:
   - Choose your input folder containing images to crop
   - Choose your output folder where cropped images will be saved

3. **Load images**:
   - Click "Load Images" to scan the input folder for image files
   - Supported formats: PNG, JPG, JPEG, BMP, TIFF, GIF

4. **Set crop area**:
   - Use the navigation buttons to browse through your images
   - Click and drag on the preview image to select the crop area
   - Or manually enter coordinates in the text fields (X, Y, Width, Height)

5. **Process images**:
   - Click "Process Images" to apply the crop to all loaded images
   - Monitor progress with the progress bar
   - Cancel processing at any time if needed

## Default Crop Settings

The application starts with default crop settings from the original `crop.sh`:
- X: 1056
- Y: 190  
- Width: 822
- Height: 947

These settings were designed for 1920x1080 screen captures of a half-vertical window.

## Tips

- The crop area is shown as a red dashed rectangle on the preview
- Crop boundaries are automatically validated to ensure they're within image bounds
- All images in the batch will use the same crop settings
- Original images are not modified - cropped versions are saved to the output folder
- Use the "Reset to Defaults" option in the File menu to restore original settings

## Keyboard Shortcuts

- `Ctrl+Q`: Quit application
- `Ctrl+T`: Test coordinates (from original capture GUI - not applicable here)

## Troubleshooting

- **"No images loaded"**: Make sure your input folder contains supported image files
- **"Pillow not available"**: Install Pillow using `pip install Pillow`
- **Processing errors**: Check that output folder is writable and has sufficient disk space