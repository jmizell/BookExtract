# Book Extract

A collection of GUI applications to automate the process of digitizing physical books into EPUB format. 
This toolchain provides user-friendly interfaces for capturing, processing, OCR, and rendering steps to convert books from 
screenshots to structured e-books.

## Overview

This project provides a complete pipeline with intuitive GUI applications for:
1. **Capturing** page screenshots from a displayed book with automated navigation
2. **Cropping** images to focus on content with interactive preview
3. **OCR Processing** to extract and clean text using AI-powered correction
4. **Rendering** the final EPUB file with proper formatting and metadata
5. **Audio Generation** (optional) using text-to-speech or full M4B audiobook creation

## Features

- **User-Friendly GUI Applications**: Intuitive interfaces replace complex command-line scripts
- **Interactive Image Processing**: Mouse-based crop selection with real-time preview
- **AI-Powered OCR Correction**: Automatically fixes OCR errors and structures content
- **Unified Intermediate Format**: Common representation for both EPUB and audiobook generation
- **Progress Tracking**: Real-time status updates and batch processing indicators
- **Flexible API Support**: Works with OpenAI, Anthropic, OpenRouter, and other compatible APIs
- **Integrated Workflow**: Seamless pipeline from screenshots to finished EPUB and M4B audiobooks
- **Error Handling**: Built-in validation and user-friendly error messages

## Prerequisites

- Linux system with X11 (for screenshot and mouse automation)
- Tesseract OCR
- Python 3.7+
- API access to a compatible AI model (supports OpenAI, Anthropic, OpenRouter, etc.)

## Installation

1. Clone this repository
2. Install required system dependencies:
   ```bash
   sudo apt-get install tesseract-ocr xdotool python3-tk
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

## Quick Start

1. **Setup**: Install dependencies and configure your `.env` file with API credentials
2. **Capture**: Run `python3 capture_gui.py` to screenshot book pages
3. **Crop**: Run `python3 crop_gui.py` to remove margins and focus on content
4. **OCR**: Run `python3 ocr_gui.py` to extract and clean text with AI
5. **Render**: Run `python3 render.py` to generate the final EPUB file

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
- Complete OCR pipeline (Tesseract OCR + AI cleanup + merge)
- Configurable API settings with connection testing
- Real-time progress tracking for batch processing
- Results preview functionality including final merged book.json
- Support for basic OCR-only or full pipeline processing
- Optional merge step to fix content split across page breaks
- AI processing to correct OCR mistakes and structure content into JSON format

### 4. Generate EPUB

Create the final e-book from the processed JSON:

```bash
python3 render.py
```

This produces an EPUB file with proper chapters, formatting, and metadata based on the structured content from the OCR processing step.

### 5. Generate Audio (Optional)

You have multiple options for creating audio versions:

#### Option A: Simple TTS (Original)
```bash
bash tts.sh
```
This generates individual WAV audio files using Kokoro TTS from the extracted text files.

#### Option B: Complete Audiobook from Intermediate Format (Recommended)
```bash
./intermediate_to_m4b.sh book_intermediate.json [output_name]
```
This creates a professional M4B audiobook directly from the intermediate format with:
- Proper metadata (title, author, genre)
- Chapter markers for easy navigation
- Combined audio in a single file
- TTS-optimized text processing
- Optimized for audiobook players

See [INTERMEDIATE_TO_M4B.md](INTERMEDIATE_TO_M4B.md) for detailed documentation.

#### Option C: Complete Audiobook from EPUB (Legacy)
```bash
./epub_to_m4b.sh your_book.epub [output_name]
```
This creates a professional M4B audiobook from EPUB files. This method is maintained for backward compatibility but the intermediate format approach (Option B) is recommended for new projects.

See [EPUB_TO_M4B.md](EPUB_TO_M4B.md) for detailed documentation.

## Intermediate Representation

BookExtract now includes a unified intermediate representation that bridges the gap between different processing pipelines. This format provides:

- **Unified Structure**: Single format that works with both EPUB and M4B generation
- **Rich Metadata**: Comprehensive book information including title, author, language, etc.
- **Structured Content**: Hierarchical organization with chapters and typed content sections
- **Format Conversion**: Seamless conversion between legacy and new formats
- **Enhanced Features**: Word counting, content analysis, and extensible design

### Key Files
- `book_intermediate.py` - Core intermediate representation module
- `intermediate_to_m4b.py` - M4B text file preparation
- `intermediate_to_m4b.sh` - Complete M4B audiobook generation
- `INTERMEDIATE_FORMAT.md` - Complete format documentation
- `INTERMEDIATE_TO_M4B.md` - M4B generation documentation

### Usage
```bash
# Generate intermediate format from render_book.py
python render_book.py  # Use GUI to save as intermediate format

# Generate intermediate format from EPUB
python epub_extractor.py book.epub --intermediate

# Convert intermediate directly to M4B audiobook (Recommended)
./intermediate_to_m4b.sh book_intermediate.json

# Convert intermediate to M4B-ready text files only
python intermediate_to_m4b.py book_intermediate.json -o m4b_ready/

# Use in render GUI
# File → Open Intermediate... or Save Intermediate As...
```

The intermediate format maintains full backward compatibility while providing enhanced structure for future development.

## Customization

- **Capture Settings**: Use the capture GUI to configure page count, navigation coordinates, and timing
- **Crop Dimensions**: Use the crop GUI's interactive preview to set optimal crop areas for your display
- **OCR Processing**: Configure API settings, models, and processing options through the OCR GUI
- **AI Prompts**: Modify the prompts within `ocr_gui.py` to improve content structuring for specific book types

## Limitations

- This toolchain is experimental and may require adjustments for specific books or layouts
- OCR quality depends on the clarity of source material and image resolution
- Complex formatting elements (tables, multi-column layouts) may not be perfectly preserved
- Currently optimized for left-to-right reading and standard book layouts
- Requires manual setup of capture coordinates for each book viewer application

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.
