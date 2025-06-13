# Book Extract

A collection of scripts to automate the process of digitizing physical books into EPUB format. 
This toolchain handles capturing, processing, OCR, and rendering steps to convert books from 
screenshots to structured e-books.

## Overview

This project provides a complete pipeline for:
1. Capturing page screenshots from a displayed book
2. Cropping images to focus on content
3. Running OCR to extract text
4. Processing with AI to fix OCR issues and structure content
5. Merging content across page breaks
6. Generating a final EPUB file

## Prerequisites

- Linux system with X11 (for screenshot and mouse automation)
- ImageMagick (for image processing)
- Tesseract OCR
- Python 3.6+
- API access to a compatible AI model (OpenAI GPT-4 Vision or equivalent)

## Installation

1. Clone this repository
2. Install required dependencies:
   ```
   sudo apt-get install imagemagick tesseract-ocr xdotool python3-tk
   pip install -r requirements.txt
   ```
   Note: `python3-tk` is needed for the GUI interface
3. Create a `.env` file with the following variables:
   ```
   API_URL=https://api.openai.com/v1/chat/completions
   API_TOKEN=your_api_key
   MODEL=gpt-4-vision-preview
   ```

## Usage

The digitization process follows these steps in sequence:

### 1. Capture Pages

Open your book in a viewer application and choose one of the capture methods:

**Option A: GUI Interface (Recommended)**
```bash
python3 capture_gui.py
# or
bash launch_capture_gui.sh
```

**Option B: Command Line**
```bash
bash capture.sh
```

The GUI version provides:
- User-friendly interface with configurable settings
- Real-time progress tracking and status updates
- Coordinate testing to ensure proper navigation
- Input validation and error handling

Both methods:
- Take screenshots of each page
- Automatically navigate to the next page
- Save images to the `images/` directory

See `README_GUI.md` for detailed GUI usage instructions.

### 2. Crop Images

Crop captured images to focus on the book content:

**Option A: GUI Interface (Recommended)**
```bash
python3 crop_gui.py
```

**Option B: Command Line**
```bash
bash crop.sh
```

The GUI version provides:
- Interactive image preview with mouse-based crop area selection
- Real-time crop preview and coordinate adjustment
- Batch processing with progress tracking
- Image navigation to review and adjust settings

Both methods remove margins and UI elements, saving cropped images to `out/` directory.

### 3. Extract Text with OCR

Extract text from cropped images using OCR:

**Option A: GUI Interface (Recommended)**
```bash
python3 ocr_gui.py
```

**Option B: Command Line**
```bash
# Basic OCR only
bash ocr.sh

# Then AI processing
python ocr.py
```

The GUI version provides:
- User-friendly interface for complete OCR pipeline (OCR + LLM cleanup + merge)
- Configurable API settings with connection testing
- Real-time progress tracking for batch processing
- Results preview functionality including final merged book.json
- Support for basic OCR-only or full pipeline processing
- Optional merge step to fix content split across page breaks

The command line approach:
1. `ocr.sh` extracts raw text using Tesseract and saves it to `.txt` files
2. `ocr.py` sends each page image and OCR text to the AI to:
   - Correct OCR mistakes
   - Format content into structured JSON
   - Identify headers, paragraphs, and other elements
3. `merge.py` (optional) fixes content split across page breaks

Note: The GUI version includes all three steps in a single interface, while the command line requires running each script separately.

### 4. Merge Content Across Pages (Command Line Only)

If using the command line approach, fix content that was split across page breaks:

```bash
python merge.py
```

This intelligently identifies and joins paragraphs that continue from one page to the next. The GUI version includes this step automatically when "Include merge step" is enabled.

### 5. Generate EPUB

Create the final e-book:

```bash
python render.py
```

This produces an EPUB file with proper chapters, formatting, and metadata.

### 6. Generate Audio (Optional)

If you want an audio version of your book:

```bash
bash tts.sh
```

This generates audio files using the Kokoro TTS engine.

## Customization

- Edit `crop.sh` to adjust cropping dimensions for your display setup
- Modify `capture.sh` to change the number of pages or capture settings
- Adjust AI prompts in `ocr.py` and `merge.py` to improve content structuring

## Limitations

- This toolchain is experimental and may require adjustments for specific books
- OCR quality depends on the clarity of source material
- Not all book formatting elements may be preserved
- Current implementation assumes left-to-right reading and standard layouts

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.
