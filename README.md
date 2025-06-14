# Book Extract

A collection of UGLY, but functional applications to automate the process of digitizing physical books into EPUB and
M4B audiobook formats. This toolchain provides interfaces for capturing, processing, OCR, editing, and rendering steps 
to convert books from screenshots to structured e-books and audiobooks.

## Overview

This project provides a complete pipeline with intuitive GUI applications for:
1. **Capturing** page screenshots from a displayed book with automated navigation
2. **Cropping** images to focus on content with interactive preview
3. **OCR Processing** to extract and clean text using Tesseract OCR and AI-powered correction
4. **Editing** the processed content and generating formatted JSON files
5. **Rendering** the final EPUB or M4B audiobook with proper formatting and metadata

## Features

- **User-Friendly GUI Applications**: Intuitive interfaces for each step of the digitization process
- **Interactive Image Processing**: Mouse-based crop selection with real-time preview
- **Multi-Stage OCR Pipeline**: Tesseract OCR + dual AI passes for maximum accuracy
- **Rich Content Editor**: Full-featured editor for refining extracted text and metadata
- **Image Rendering Support**: Real image display in preview panels with automatic resizing and format support
- **Dual Export Options**: Generate both EPUB e-books and M4B audiobooks from the same source
- **Unified Intermediate Format**: JSON-based format ensures consistency across output types
- **Progress Tracking**: Real-time status updates and batch processing indicators
- **Flexible API Support**: Works with OpenAI, Anthropic, OpenRouter, and other compatible APIs
- **Integrated Workflow**: Seamless pipeline from screenshots to finished publications
- **Error Handling**: Built-in validation and user-friendly error messages

## Prerequisites

- Linux system with X11 (for screenshot and mouse automation)
- Python 3 interpreter
- Tesseract OCR
- ImageMagick (import command)
- xdotool (for mouse automation)
- API access to a compatible AI model (supports OpenAI, Anthropic, OpenRouter, etc.)
- For M4B audiobook generation:
  - Kokoro TTS (text-to-speech engine)
  - FFmpeg (audio processing)
  - FFprobe (media analysis)

## Installation

1. Clone this repository
2. Install required system dependencies:
   ```bash
   sudo apt-get install python3 python3-tk tesseract-ocr imagemagick xdotool ffmpeg
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on the example:
   ```bash
   cp .env-example .env
   ```
   Then edit `.env` with your API credentials:
   ```
   API_TOKEN="your_api_key_here"
   MODEL="anthropic/claude-3.7-sonnet"
   API_URL="https://openrouter.ai/api/v1/chat/completions"
   ```

**Note**: The `kokoro` package provides the TTS engine, while `ffmpeg` includes both FFmpeg and FFprobe for audio 
processing and media analysis. ImageMagick provides the `import` command used for screenshot capture.

## Quick Start

1. **Setup**: Install dependencies and configure your `.env` file with API credentials
2. **Capture**: Run `python3 capture_gui.py` to screenshot book pages
3. **Crop**: Run `python3 crop_gui.py` to remove margins and focus on content
4. **OCR**: Run `python3 ocr_gui.py` to extract and clean text with Tesseract OCR and AI
5. **Edit**: Run `python3 edit_gui.py` to edit content, preview with image rendering, and generate formatted JSON files
6. **Export**: Run `python3 render_epub.py` for EPUB or `python3 render_m4b.py` for M4B audiobook

## Usage

The digitization process follows these steps in sequence using the GUI applications:

### 1. Capture Pages

Open your book in a viewer application and run the capture tool:

```bash
python3 capture_gui.py
```

The capture GUI provides:
- User-friendly interface with configurable settings
- Real-time progress tracking and status updates
- Coordinate testing to ensure proper navigation
- Input validation and error handling
- Automatic screenshot capture with page navigation
- Saves images to the `images/` directory

### 2. Crop Images

Crop captured images to focus on the book content:

```bash
python3 crop_gui.py
```

The crop GUI provides:
- Interactive image preview with mouse-based crop area selection
- Real-time crop preview and coordinate adjustment
- Batch processing with progress tracking
- Image navigation to review and adjust settings
- Removes margins and UI elements, saving cropped images to `out/` directory

### 3. Extract Text with OCR

Extract text from cropped images using OCR and AI processing:

```bash
python3 ocr_gui.py
```

The OCR GUI provides:
- Complete OCR pipeline with three processing stages:
  1. **Tesseract OCR**: Initial text extraction from images
  2. **AI Second Pass**: LLM-powered OCR correction and improvement
  3. **AI Final Pass**: Content cleanup and merging across page breaks
- Configurable API settings with connection testing
- Real-time progress tracking for batch processing
- Results preview functionality including final merged content
- Support for basic OCR-only or full pipeline processing
- AI processing to correct OCR mistakes and structure content

### 4. Edit and Format Content

Edit the processed content and generate formatted JSON files:

```bash
python3 edit_gui.py
```

The edit GUI provides:
- Rich text editor for reviewing and editing extracted content
- JSON structure editing with validation
- Real-time preview of formatted content with actual image rendering
- Metadata editing (title, author, chapters, etc.)
- Export to intermediate JSON format for rendering
- Image preview and management with support for PNG, JPEG, GIF, and BMP formats
- Content organization and chapter structuring
- Cover image and content image integration

### 5. Export Final Format

Generate the final e-book or audiobook from the formatted JSON:

#### For EPUB E-books:
```bash
python3 render_epub.py
```

#### For M4B Audiobooks:
```bash
python3 render_m4b.py
```

Both export tools provide:
- Loading of intermediate JSON format files
- Metadata configuration and validation
- Progress tracking during generation
- Preview capabilities
- Professional formatting with proper chapters and structure

## Workflow Summary

The complete BookExtract workflow follows this sequence:

1. **capture_gui.py** → Capture page images from displayed books
2. **crop_gui.py** → Crop images to focus on content
3. **ocr_gui.py** → Extract text using Tesseract OCR + AI processing (3 passes)
4. **edit_gui.py** → Edit content with image rendering preview and generate formatted JSON files
5. **render_epub.py** OR **render_m4b.py** → Export to EPUB or M4B audiobook

## Intermediate JSON Format

BookExtract uses a unified intermediate JSON representation that bridges the gap between OCR processing and final output generation. This format provides:

- **Unified Structure**: Single format that works with both EPUB and M4B generation
- **Rich Metadata**: Comprehensive book information including title, author, language, etc.
- **Structured Content**: Hierarchical organization with chapters and typed content sections
- **Image Support**: Native support for cover images and content images with captions
- **Format Conversion**: Seamless conversion between different processing stages
- **Enhanced Features**: Word counting, content analysis, and extensible design

### Image Integration in JSON Format

The intermediate JSON format supports two types of images:

#### Cover Images
```json
{
  "type": "cover",
  "image": "cover.png"
}
```

#### Content Images
```json
{
  "type": "image",
  "image": "photo.jpg",
  "caption": "Optional caption text"
}
```

**Supported Image Formats**: PNG, JPEG, GIF, and BMP
**File Placement**: Images should be placed in the same directory as the JSON file or use relative paths
**Resolution Guidelines**: 
- Cover images: Recommended 600x800 pixels or similar book cover ratio
- Content images: Any reasonable resolution (automatically resized for display)

## Customization

- **Capture Settings**: Use the capture GUI to configure page count, navigation coordinates, and timing
- **Crop Dimensions**: Use the crop GUI's interactive preview to set optimal crop areas for your display
- **OCR Processing**: Configure API settings, models, and processing options through the OCR GUI
- **Content Editing**: Use the edit GUI to refine extracted text, organize chapters, and adjust metadata
- **Export Options**: Configure output settings in the render GUIs for EPUB and M4B formats
- **AI Prompts**: Modify the prompts within `ocr_gui.py` to improve content structuring for specific book types

## Troubleshooting

### Image Rendering Issues
- **Image Not Displaying**: Check that the image file exists in the specified path and verify the format is supported (PNG, JPEG, GIF, BMP)
- **Performance Issues**: Use the "Refresh" button to clear the image cache, or consider resizing very large images
- **Error Messages**: 
  - `[IMAGE: filename - NOT FOUND]`: File doesn't exist at the specified path
  - `[IMAGE: filename - LOAD FAILED]`: File exists but couldn't be loaded (possibly corrupted or unsupported format)

### General Issues
- Ensure all dependencies are properly installed, especially Pillow (PIL) for image processing
- Check file permissions for image files and directories
- For memory issues with large images, close and reopen the tool

## Limitations

- This toolchain is experimental and may require adjustments for specific books or layouts
- OCR quality depends on the clarity of source material and image resolution
- Complex formatting elements (tables, multi-column layouts) may not be perfectly preserved
- Currently optimized for left-to-right reading and standard book layouts
- Requires manual setup of capture coordinates for each book viewer application
- Image files should be kept under 5MB for optimal performance

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.
