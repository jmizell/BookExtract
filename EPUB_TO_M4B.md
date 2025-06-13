# EPUB to M4B Audiobook Converter

This tool converts EPUB files to M4B audiobooks with proper metadata and chapter markers. It reads the EPUB content chapter by chapter, generates audio using text-to-speech (TTS), and combines everything into a single M4B audiobook file.

## Features

- **Complete EPUB Processing**: Extracts text content from EPUB files while preserving chapter structure
- **High-Quality TTS**: Uses Kokoro TTS for natural-sounding speech synthesis
- **Professional M4B Output**: Creates M4B audiobooks with:
  - Proper metadata (title, author, genre)
  - Chapter markers for easy navigation
  - Optimized audio quality (64kbps AAC)
- **Title Page Support**: Automatically creates a title page with book and author information
- **Chapter Detection**: Intelligently identifies chapter titles from EPUB structure
- **Progress Tracking**: Real-time status updates during conversion
- **Error Handling**: Comprehensive error checking and user-friendly messages

## Requirements

### System Dependencies
- Linux system (tested on Debian/Ubuntu)
- Python 3.7+
- ffmpeg
- Kokoro TTS

### Python Dependencies
- EbookLib
- BeautifulSoup4
- All dependencies from requirements.txt

## Installation

1. **Install system dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install ffmpeg python3-pip
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Kokoro TTS installation:**
   ```bash
   kokoro --help
   ```

## Usage

### Basic Usage

```bash
./epub_to_m4b.sh <epub_file> [output_name]
```

### Examples

```bash
# Convert with automatic naming
./epub_to_m4b.sh "My Book.epub"

# Convert with custom output name
./epub_to_m4b.sh "My Book.epub" "My_Custom_Audiobook"

# The output will be "My_Custom_Audiobook.m4b"
```

### Command Line Options

- `epub_file`: Path to the EPUB file to convert (required)
- `output_name`: Custom name for the output M4B file (optional, defaults to EPUB filename)

## How It Works

### 1. EPUB Text Extraction (`epub_extractor.py`)

The script first extracts text content from the EPUB file:

- Reads EPUB metadata (title, author, language)
- Creates a title page with book information
- Extracts text from each chapter while preserving structure
- Cleans and normalizes text for optimal TTS processing
- Saves extracted content as individual text files
- Generates a JSON file with book information and chapter details

### 2. Audio Generation

For each text file (title page + chapters):

- Uses Kokoro TTS with the `am_michael` voice model
- Generates high-quality WAV audio files
- Processes files in sequential order to maintain chapter structure

### 3. M4B Creation

The final step combines everything into a professional audiobook:

- Creates chapter metadata with precise timing information
- Combines all audio files using ffmpeg
- Adds comprehensive metadata (title, author, album, genre)
- Generates chapter markers for navigation
- Outputs optimized M4B file with AAC encoding

## Configuration

### TTS Settings

You can modify TTS settings in `epub_to_m4b.sh`:

```bash
TTS_MODEL="am_michael"  # Kokoro TTS model
TTS_LANG="a"           # Language setting
AUDIO_BITRATE="64k"    # Audio bitrate for M4B
SAMPLE_RATE="22050"    # Sample rate for audio
```

### Audio Quality

The script uses optimized settings for audiobooks:
- **Codec**: AAC (LC)
- **Bitrate**: 64kbps (good quality, reasonable file size)
- **Sample Rate**: 22.05kHz (sufficient for speech)
- **Channels**: Mono (standard for audiobooks)

## Output Structure

The generated M4B file includes:

1. **Title Page**: Book title and author information
2. **Chapters**: Each chapter from the EPUB with proper titles
3. **Metadata**: Complete book information
4. **Chapter Markers**: Precise navigation points

### Example Chapter Structure
```
00:00:00 - Title Page
00:00:04 - Introduction  
00:00:26 - Chapter One: The Beginning
00:00:53 - Chapter Two: Advanced Topics
00:01:16 - Conclusion
```

## File Management

### Temporary Files

The script creates temporary directories during processing:
- `epub_temp_XXXX/`: Extracted EPUB content
- `audio_temp_XXXX/`: Generated audio files

These are automatically cleaned up after successful conversion.

### Output Files

- `[output_name].m4b`: Final audiobook file
- Temporary files are removed automatically

## Troubleshooting

### Common Issues

1. **"EPUB file not found"**
   - Check the file path and ensure the EPUB file exists
   - Use absolute paths if needed

2. **"Kokoro TTS not found"**
   - Install Kokoro TTS: `pip install kokoro`
   - Ensure it's in your PATH

3. **"ffmpeg not found"**
   - Install ffmpeg: `sudo apt-get install ffmpeg`

4. **"Failed to extract EPUB content"**
   - Verify the EPUB file is not corrupted
   - Check file permissions

5. **Audio generation fails**
   - Ensure sufficient disk space
   - Check that text files contain valid content

### Debug Mode

For troubleshooting, you can run individual components:

```bash
# Test EPUB extraction only
python3 epub_extractor.py your_book.epub -o test_output

# Test TTS generation
kokoro -m am_michael -l a -i test_file.txt -o test_audio.wav
```

## Performance

### Processing Time

Conversion time depends on:
- Book length (number of chapters and words)
- System performance (CPU, RAM)
- TTS model complexity

Typical processing times:
- Short book (100 pages): 5-10 minutes
- Medium book (300 pages): 15-30 minutes
- Long book (500+ pages): 30-60 minutes

### Resource Usage

- **CPU**: Intensive during TTS generation
- **RAM**: ~2-4GB during processing
- **Disk**: Temporary files require 2-3x final file size
- **Network**: Initial model downloads (~500MB)

## Advanced Usage

### Batch Processing

For multiple books, create a simple loop:

```bash
for epub in *.epub; do
    ./epub_to_m4b.sh "$epub"
done
```

### Custom Voice Models

To use different Kokoro TTS voices, modify the `TTS_MODEL` variable in the script:

```bash
TTS_MODEL="am_sarah"    # Female voice
TTS_MODEL="am_michael"  # Male voice (default)
```

### Quality Settings

For higher quality output, adjust these settings:

```bash
AUDIO_BITRATE="128k"   # Higher bitrate
SAMPLE_RATE="44100"    # CD quality sample rate
```

Note: Higher quality settings result in larger file sizes.

## Integration with BookExtract Workflow

This tool integrates seamlessly with the existing BookExtract pipeline:

1. **Capture**: Use `capture_gui.py` to screenshot book pages
2. **Crop**: Use `crop_gui.py` to remove margins
3. **OCR**: Use `ocr_gui.py` to extract and clean text
4. **Render**: Use `render.py` to generate EPUB
5. **Audio**: Use `epub_to_m4b.sh` to create audiobook

## License

This tool is part of the BookExtract project and is licensed under the GNU General Public License v3.0.

## Support

For issues, questions, or contributions, please refer to the main BookExtract repository.