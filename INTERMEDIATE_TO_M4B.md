# Intermediate to M4B Audiobook Converter

This tool converts book intermediate representation files directly to M4B audiobooks with proper metadata and chapter markers. It works solely with the intermediate format, providing a streamlined pipeline from structured book data to professional audiobooks.

## Features

- **Direct Intermediate Processing**: Works directly with intermediate format files (no EPUB required)
- **High-Quality TTS**: Uses Kokoro TTS for natural-sounding speech synthesis
- **Professional M4B Output**: Creates M4B audiobooks with:
  - Proper metadata (title, author, genre)
  - Chapter markers for easy navigation
  - Optimized audio quality (64kbps AAC)
- **TTS-Optimized Text Processing**: Automatically cleans and formats text for optimal TTS output
- **Title Page Support**: Automatically creates a title page with book and author information
- **Smart Chapter Detection**: Uses intermediate format structure for precise chapter organization
- **Progress Tracking**: Real-time status updates during conversion
- **Error Handling**: Comprehensive error checking and user-friendly messages

## Requirements

### System Dependencies
- Linux system (tested on Debian/Ubuntu)
- Python 3.7+
- ffmpeg
- Kokoro TTS

### Python Dependencies
- book_intermediate module (included in BookExtract)
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
./intermediate_to_m4b.sh <intermediate_file> [output_name]
```

### Examples

```bash
# Convert with automatic naming
./intermediate_to_m4b.sh book_intermediate.json

# Convert with custom output name
./intermediate_to_m4b.sh book_intermediate.json "My_Custom_Audiobook"

# The output will be "My_Custom_Audiobook.m4b"
```

### Command Line Options

- `intermediate_file`: Path to the intermediate JSON file to convert (required)
- `output_name`: Custom name for the output M4B file (optional, defaults to book title)

## How It Works

### 1. Intermediate Format Processing (`intermediate_to_m4b.py`)

The script processes the intermediate representation:

- Validates the intermediate format structure
- Extracts book metadata (title, author, language)
- Creates a title page with book information
- Processes each chapter with TTS-optimized formatting:
  - Cleans text for better pronunciation
  - Handles different content types (paragraphs, headers, quotes)
  - Manages image descriptions and special formatting
  - Ensures proper punctuation and spacing
- Generates individual text files for each chapter
- Creates a legacy-compatible metadata file

### 2. Audio Generation

For each text file (title page + chapters):

- Uses Kokoro TTS with the `am_michael` voice model
- Generates high-quality WAV audio files
- Processes files in sequential order to maintain chapter structure
- Skips empty chapters automatically

### 3. M4B Creation

The final step combines everything into a professional audiobook:

- Creates chapter metadata with precise timing information
- Combines all audio files using ffmpeg
- Adds comprehensive metadata (title, author, album, genre)
- Generates chapter markers for navigation
- Outputs optimized M4B file with AAC encoding

## Input Format

The tool expects intermediate format files created by:
- `render_book.py` (Book Renderer GUI)
- `book_intermediate.py` conversion tools
- Any tool that outputs the BookExtract intermediate format

### Required Structure

```json
{
  "metadata": {
    "title": "Book Title",
    "author": "Author Name",
    "language": "en"
  },
  "chapters": [
    {
      "number": 1,
      "title": "Chapter Title",
      "sections": [
        {
          "type": "paragraph",
          "content": "Chapter content..."
        }
      ]
    }
  ],
  "format_version": "1.0"
}
```

## Configuration

### TTS Settings

You can modify TTS settings in `intermediate_to_m4b.sh`:

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
2. **Chapters**: Each chapter from the intermediate format with proper titles
3. **Metadata**: Complete book information
4. **Chapter Markers**: Precise navigation points

### Example Chapter Structure
```
00:00:00 - Title Page
00:00:04 - Chapter 1: Introduction  
00:00:26 - Chapter 2: The Beginning
00:00:53 - Chapter 3: Advanced Topics
00:01:16 - Chapter 4: Conclusion
```

## Text Processing Features

### TTS Optimization

The tool automatically optimizes text for TTS:

- **Punctuation Normalization**: Fixes ellipses, dashes, and quotes
- **Sentence Spacing**: Ensures proper pauses between sentences
- **Character Cleanup**: Removes problematic characters and HTML tags
- **Smart Quotes**: Converts smart quotes to regular quotes
- **Proper Endings**: Ensures sentences end with appropriate punctuation

### Content Type Handling

Different content types are processed appropriately:

- **Paragraphs**: Standard text with proper spacing
- **Headers**: Extra spacing for emphasis
- **Bold Text**: Preserved emphasis
- **Block Quotes**: Special formatting with indentation
- **Images**: Converted to descriptive text
- **Page Divisions**: Converted to natural pauses

## File Management

### Temporary Files

The script creates temporary directories during processing:
- `m4b_temp_XXXX/`: Processed text files and metadata
- `audio_temp_XXXX/`: Generated audio files

These are automatically cleaned up after successful conversion.

### Output Files

- `[output_name].m4b`: Final audiobook file
- Temporary files are removed automatically

## Troubleshooting

### Common Issues

1. **"Intermediate file not found"**
   - Check the file path and ensure the intermediate file exists
   - Use absolute paths if needed

2. **"Invalid intermediate file format"**
   - Verify the JSON structure matches the expected format
   - Check for required fields (metadata, chapters, title, author)

3. **"Kokoro TTS not found"**
   - Install Kokoro TTS: `pip install kokoro`
   - Ensure it's in your PATH

4. **"ffmpeg not found"**
   - Install ffmpeg: `sudo apt-get install ffmpeg`

5. **"Failed to process intermediate format"**
   - Verify the intermediate file is valid JSON
   - Check file permissions
   - Ensure chapters have content

6. **Audio generation fails**
   - Ensure sufficient disk space
   - Check that text files contain valid content
   - Verify Kokoro TTS is working: `kokoro --help`

### Debug Mode

For troubleshooting, you can run individual components:

```bash
# Test intermediate processing only
python3 intermediate_to_m4b.py book_intermediate.json -o test_output

# Test TTS generation
kokoro -m am_michael -l a -i test_file.txt -o test_audio.wav

# Validate intermediate file
python3 -c "
from book_intermediate import BookIntermediate
book = BookIntermediate.load_from_file('book_intermediate.json')
print(f'Valid: {book.metadata.title} by {book.metadata.author}')
"
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
for intermediate in *.json; do
    ./intermediate_to_m4b.sh "$intermediate"
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

This tool integrates seamlessly with the BookExtract pipeline:

1. **Capture**: Use `capture_gui.py` to screenshot book pages
2. **Crop**: Use `crop_gui.py` to remove margins
3. **OCR**: Use `ocr_gui.py` to extract and clean text
4. **Render**: Use `render_book.py` to create intermediate format
5. **Audio**: Use `intermediate_to_m4b.sh` to create audiobook

### Alternative Workflows

You can also start from other formats:

```bash
# From EPUB (via intermediate format)
python3 epub_extractor.py book.epub -o temp --intermediate
./intermediate_to_m4b.sh temp/book_intermediate.json

# From section array
python3 book_intermediate.py --convert-from-sections sections.json -o intermediate.json
./intermediate_to_m4b.sh intermediate.json
```

## Comparison with EPUB-based Workflow

### Advantages of Intermediate Format

1. **Direct Processing**: No EPUB extraction step required
2. **Better Structure**: Preserves detailed content structure and formatting
3. **Optimized Text**: Built-in TTS optimization and text cleaning
4. **Flexible Input**: Can work with any source that produces intermediate format
5. **Consistent Results**: Standardized processing regardless of input source

### Migration from EPUB Workflow

If you have existing EPUB files:

```bash
# Convert EPUB to intermediate format first
python3 epub_extractor.py book.epub -o temp --intermediate

# Then use the new workflow
./intermediate_to_m4b.sh temp/book_intermediate.json
```

## License

This tool is part of the BookExtract project and is licensed under the GNU General Public License v3.0.

## Support

For issues, questions, or contributions, please refer to the main BookExtract repository.