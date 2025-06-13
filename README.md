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
   sudo apt-get install imagemagick tesseract-ocr xdotool
   pip install ebooklib python-dotenv requests
   ```
3. Create a `.env` file with the following variables:
   ```
   API_URL=https://api.openai.com/v1/chat/completions
   API_TOKEN=your_api_key
   MODEL=gpt-4-vision-preview
   ```

## Usage

The digitization process follows these steps in sequence:

### 1. Capture Pages

Open your book in a viewer application and run:

```bash
bash capture.sh
```

This script:
- Takes screenshots of each page
- Automatically navigates to the next page
- Saves images to the `images/` directory

### 2. Crop Images

Crop captured images to focus on the book content:

```bash
bash crop.sh
```

This script removes margins and UI elements, saving cropped images to `out/` directory.

### 3. Extract Text with OCR

Run OCR on the cropped images:

```bash
bash ocr.sh
```

This extracts raw text using Tesseract and saves it to `.txt` files.

### 4. Process with AI

Enhance OCR results and structure the content:

```bash
python ocr.py
```

This script:
- Sends each page image and OCR text to the AI
- Corrects OCR mistakes
- Formats content into structured JSON
- Identifies headers, paragraphs, and other elements

### 5. Merge Content Across Pages

Fix content that was split across page breaks:

```bash
python merge.py
```

This intelligently identifies and joins paragraphs that continue from one page to the next.

### 6. Generate EPUB

Create the final e-book:

```bash
python render.py
```

This produces an EPUB file with proper chapters, formatting, and metadata.

### 7. Generate Audio (Optional)

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
