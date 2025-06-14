# EPUB Renderer Tool

## Overview

The `render_epub.py` is a specialized tkinter-based GUI application for generating EPUB files from intermediate format data. This tool focuses specifically on reading intermediate format files and converting them to EPUB format.

## Features

### Main Interface Layout
- **Left Panel**: Book Information display showing metadata and chapter organization
- **Right Panel**: EPUB Preview showing rendered content
- **Bottom Panel**: Log Console for real-time feedback and debugging

### Book Information (Left Panel)
- Display book metadata (title, author, language, word count)
- Chapter list with word count breakdown
- Load intermediate format files
- Export EPUB functionality

### EPUB Preview (Right Panel)
- Live preview of EPUB content as plain text
- Automatic refresh when intermediate file is loaded
- Chapter-by-chapter content display
- Generated from intermediate format data

### Log Console (Bottom Panel)
- Real-time logging of all operations
- Timestamped messages with severity levels
- Clear log functionality
- Scrollable history

## Menu System

### File Menu
- **Open Intermediate** (Ctrl+O): Load intermediate format file
- **Export EPUB** (Ctrl+E): Generate and save EPUB file
- **Exit** (Ctrl+Q): Close application

### View Menu
- **Refresh Preview** (F5): Update EPUB preview
- **Open EPUB in Browser** (Ctrl+B): Open generated EPUB file
- **Clear Log**: Clear the log console

### Help Menu
- **About**: Application information
- **Intermediate Format Help**: Documentation on intermediate format structure

## Intermediate Format Support

The EPUB Renderer works with BookExtract intermediate format files:

### Supported File Types
- `.json` files containing intermediate format data
- Files created by `epub_extractor.py` with `--intermediate` flag
- Files saved from `render_book.py` as intermediate format

### File Structure
The intermediate format contains:
- Book metadata (title, author, language, etc.)
- Organized chapters with content sections
- Word count and chapter statistics

## Key Features

### 1. Metadata Display
- Book title, author, and language information
- Chapter count and total word count
- Chapter-by-chapter word count breakdown
- File path information

### 2. Live Preview
- Generates temporary EPUB files
- Extracts and displays readable content
- Updates automatically when intermediate file is loaded

### 3. File Management
- Supports relative image paths from intermediate file location
- Handles missing files gracefully with placeholders
- Automatic EPUB generation and export

### 4. Error Handling
- Comprehensive error messages
- Graceful degradation for missing resources
- User-friendly error reporting

### 5. Keyboard Shortcuts
- Open intermediate file (Ctrl+O)
- Export EPUB (Ctrl+E)
- Quick preview refresh (F5)

## Usage Instructions

### Starting the Application
```bash
cd /workspace/BookExtract
python render_epub.py
```

### Basic Workflow
1. **Load Intermediate File**: Use File → Open Intermediate to load an intermediate format file
2. **Review Metadata**: Check book information and chapter organization in the left panel
3. **Preview**: The EPUB preview will automatically generate and display in the right panel
4. **Export**: Use File → Export EPUB to save the final EPUB file

### Supported Input Files
The EPUB Renderer accepts intermediate format files created by:
- `epub_extractor.py` with `--intermediate` flag
- `render_book.py` when saving as intermediate format
- Any tool that generates BookExtract intermediate format

### Example Workflow
1. Extract content using `epub_extractor.py --intermediate book.epub`
2. Open the generated intermediate file in `render_epub.py`
3. Review the book metadata and chapter organization
4. Export as EPUB for distribution

## Technical Implementation

### Core Components
- **EpubRenderer Class**: Main application controller
- **Intermediate Format Loading**: Uses BookIntermediate class
- **EPUB Generation**: Converts intermediate format to EPUB
- **Preview System**: Extracts and displays EPUB content
- **Logging System**: Real-time operation feedback

### Dependencies
- tkinter (built-in with Python)
- ebooklib (for EPUB generation)
- book_intermediate (BookExtract intermediate format support)
- tempfile (for preview generation)
- threading (for non-blocking operations)

### File Structure
```
BookExtract/
├── render_epub.py         # EPUB Renderer application
├── book_intermediate.py   # Intermediate format support
├── out/                   # Default input/output directory
│   ├── *.intermediate.json # Intermediate format files
│   └── *.png              # Cover and content images
└── requirements.txt       # Python dependencies
```

## Testing

The application has been tested with:
- ✅ Intermediate format loading and parsing
- ✅ EPUB generation from intermediate data
- ✅ Preview extraction and display
- ✅ File load/export operations
- ✅ Error handling for invalid intermediate files
- ✅ Missing image file handling

## Advantages Over Command Line

1. **Visual Interface**: Clear display of book metadata and structure
2. **Immediate Preview**: Real-time EPUB generation and preview
3. **Error Prevention**: GUI provides clear feedback on issues
4. **Ease of Use**: No need to remember command-line syntax
5. **Integrated Workflow**: Load, preview, and export in one interface

## Future Enhancements

Potential improvements could include:
- Enhanced EPUB viewer integration
- Batch processing capabilities
- Advanced metadata editing
- Chapter reordering interface
- Image preview in the interface

The EPUB Renderer provides a specialized, user-friendly interface for converting intermediate format files to EPUB, focusing on the final publishing stage of the BookExtract workflow.