# EPUB Loading Feature Implementation

## Overview

This implementation adds the ability to load EPUB files directly into the edit_gui.py editor as JSON section arrays. Users can now open EPUB files, edit their content in the familiar JSON format, and save them back as intermediate files or export as new EPUBs.

## Features Added

### 1. EPUB Reading Capability (`BookConverter.from_epub_file`)

**Location**: `bookextract/book_intermediate.py`

**New Method**: `BookConverter.from_epub_file(epub_path, extract_images=True, output_dir=None)`

**Functionality**:
- Reads EPUB files using the existing `ebooklib` dependency
- Extracts metadata (title, author, language, identifier)
- Extracts and saves cover images
- Processes HTML content into structured sections
- Maintains chapter organization and reading order
- Converts HTML elements to appropriate section types:
  - `<h1>` → `chapter_header` or `header`
  - `<h2>` → `header`
  - `<h3-h6>` → `sub_header`
  - `<p>` → `paragraph`
  - `<strong>/<b>` → `bold` (when entire paragraph is bold)
  - `<blockquote>` → `block_indent`
  - Indented content → `block_indent`
  - `<img>` → `image` sections

### 2. GUI Integration (`edit_gui.py`)

**New Menu Option**: File > Open EPUB...

**New Toolbar Button**: "Open EPUB"

**New Method**: `open_epub()`

**Functionality**:
- File dialog to select EPUB files
- Loads EPUB using `BookConverter.from_epub_file`
- Converts to section array format
- Populates JSON editor with formatted content
- Applies syntax highlighting
- Updates preview panel
- Logs progress and statistics

### 3. Enhanced Help Documentation

**Updated**: JSON Format Help dialog

**New Content**: 
- Instructions for loading EPUB files
- Explanation of EPUB conversion process
- Feature list for EPUB loading

## Usage Instructions

### For End Users

1. **Open the Editor**:
   ```bash
   python edit_gui.py
   ```

2. **Load an EPUB**:
   - Click the "Open EPUB" button, or
   - Use File > Open EPUB... menu option
   - Select an EPUB file from the file dialog

3. **Edit Content**:
   - The EPUB content appears as editable JSON in the left panel
   - Use the rich text preview on the right to see formatted output
   - Edit sections as needed using the standard JSON format

4. **Save Results**:
   - Save as JSON: File > Save JSON As...
   - Save as Intermediate: File > Save Intermediate As...
   - Export as new EPUB: Use render_epub.py

### For Developers

```python
from bookextract import BookConverter

# Load EPUB file
intermediate = BookConverter.from_epub_file(
    "path/to/book.epub",
    extract_images=True,
    output_dir="./extracted_images"
)

# Convert to section array for editing
sections = BookConverter.to_section_array(intermediate)

# sections is now a list of dictionaries ready for JSON editing
```

## Technical Details

### Dependencies

- `ebooklib==0.19` (already in requirements.txt)
- `beautifulsoup4>=4.9.0` (already in requirements.txt)

### File Structure

```
bookextract/
├── book_intermediate.py     # Enhanced with EPUB reading
└── ...

edit_gui.py                  # Enhanced with EPUB loading UI
```

### EPUB Item Type Mapping

The implementation correctly handles ebooklib item types:
- Type 9: HTML documents (chapters)
- Type 10: Cover images
- Type 1: Regular images
- Type 4: NCX files (ignored)

### HTML Content Processing

The HTML parser intelligently converts content:
- Preserves document structure
- Maintains reading order
- Handles nested elements appropriately
- Extracts meaningful content while ignoring navigation/styling elements

## Workflow Integration

### Complete Round-Trip Support

1. **JSON → EPUB** (existing): `render_epub.py`
2. **EPUB → JSON** (new): `edit_gui.py` with "Open EPUB"
3. **JSON ↔ Intermediate** (existing): `edit_gui.py`

### Image Handling

- Cover images are extracted and saved with descriptive names
- Content images are referenced but may need manual extraction
- Image paths are preserved in the JSON structure
- Missing images are handled gracefully with warnings

## Error Handling

- Comprehensive error handling for malformed EPUBs
- Graceful degradation for missing metadata
- User-friendly error messages in the GUI
- Detailed logging for debugging

## Testing

The implementation has been thoroughly tested with:
- Round-trip conversion (JSON → EPUB → JSON)
- Various EPUB structures and content types
- Error conditions and edge cases
- GUI integration and user workflows

## Future Enhancements

Potential improvements for future versions:
- Enhanced image extraction from EPUB internal resources
- Support for more complex HTML structures
- Table of contents preservation
- Custom CSS style preservation
- Batch EPUB processing

## Compatibility

- Compatible with existing BookExtract workflows
- Maintains backward compatibility with all existing features
- Uses existing dependencies (no new requirements)
- Follows established code patterns and conventions