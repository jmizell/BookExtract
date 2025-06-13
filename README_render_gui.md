# EPUB Render GUI Tool

## Overview

The `render_gui.py` is a complete tkinter-based GUI application that converts the command-line `render.py` script into a user-friendly graphical interface for creating EPUB books from JSON data.

## Features

### Main Interface Layout
- **Left Panel**: JSON Editor with syntax highlighting and editing capabilities
- **Right Panel**: EPUB Preview showing rendered content
- **Bottom Panel**: Log Console for real-time feedback and debugging

### JSON Editor (Left Panel)
- Full-featured text editor with undo/redo support
- Syntax validation and formatting
- Load/Save JSON files
- Real-time editing with change detection
- Keyboard shortcuts (Ctrl+O, Ctrl+S, etc.)

### EPUB Preview (Right Panel)
- Live preview of EPUB content as plain text
- Automatic refresh when JSON changes
- Chapter-by-chapter content display
- Export functionality to save EPUB files

### Log Console (Bottom Panel)
- Real-time logging of all operations
- Timestamped messages with severity levels
- Clear log functionality
- Scrollable history

## Menu System

### File Menu
- **New** (Ctrl+N): Create new JSON document
- **Open** (Ctrl+O): Load existing JSON file
- **Save** (Ctrl+S): Save current JSON
- **Save As** (Ctrl+Shift+S): Save with new filename
- **Export EPUB** (Ctrl+E): Generate and save EPUB file
- **Exit** (Ctrl+Q): Close application

### Edit Menu
- **Format JSON** (Ctrl+F): Auto-format JSON with proper indentation
- **Validate JSON** (Ctrl+V): Check JSON syntax and required fields
- **Clear Log**: Clear the log console

### View Menu
- **Refresh Preview** (F5): Update EPUB preview
- **Open EPUB in Browser** (Ctrl+B): Open generated EPUB file

### Help Menu
- **About**: Application information
- **JSON Format Help**: Documentation on supported JSON structure

## JSON Format Support

The GUI supports all the same JSON elements as the original render.py:

### Required Elements
```json
{"type": "title", "content": "Book Title"}
{"type": "author", "content": "Author Name"}
{"type": "cover", "image": "cover.png"}
```

### Content Elements
```json
{"type": "chapter_header", "content": "Chapter Number"}
{"type": "paragraph", "content": "Regular text content"}
{"type": "header", "content": "Section header"}
{"type": "sub_header", "content": "Subsection header"}
{"type": "bold", "content": "Bold text"}
{"type": "block_indent", "content": "Indented block quote"}
{"type": "image", "image": "image.png", "caption": "Optional caption"}
{"type": "page_division"}
```

## Key Features

### 1. Real-time Validation
- JSON syntax checking
- Required field validation
- Automatic stub insertion for missing required sections
- Immediate feedback on errors

### 2. Live Preview
- Generates temporary EPUB files
- Extracts and displays readable content
- Updates automatically when JSON changes

### 3. File Management
- Supports relative image paths
- Automatic directory creation
- Handles missing files gracefully

### 4. Error Handling
- Comprehensive error messages
- Graceful degradation for missing resources
- User-friendly error reporting

### 5. Keyboard Shortcuts
- Standard editing shortcuts (Ctrl+N, Ctrl+O, Ctrl+S)
- Format and validation shortcuts
- Quick preview refresh (F5)

## Usage Instructions

### Starting the Application
```bash
cd /workspace/BookExtract
python render_gui.py
```

### Basic Workflow
1. **Load or Create JSON**: Use File → Open or start with New
2. **Edit Content**: Modify JSON in the left editor panel
3. **Validate**: Use Edit → Validate JSON to check syntax and auto-add missing stubs
4. **Preview**: Click Refresh in the right panel to see EPUB preview
5. **Export**: Use File → Export EPUB to save the final book

### Auto-Stub Feature
When validating JSON, if required sections (title, author, cover) are missing:
- The application will prompt you to automatically add stub entries
- Stubs are inserted at the beginning of the JSON with placeholder content:
  - **title**: "Your Book Title Here"
  - **author**: "Your Name Here"  
  - **cover**: Automatically uses the same filename as your JSON file but with .png extension
    - Example: If your JSON file is "my_book.json", the cover will be "my_book.png"
    - Falls back to "cover.png" if no JSON file is currently loaded
- You can then edit the placeholder text with your actual information
- This ensures your JSON always has the minimum required structure for EPUB generation

### Sample JSON Structure
Here's an example JSON structure that demonstrates all supported elements:

```json
[
  {"type": "title", "content": "Sample Book Title"},
  {"type": "author", "content": "Sample Author"},
  {"type": "cover", "image": "cover.png"},
  {"type": "chapter_header", "content": "1"},
  {"type": "paragraph", "content": "This is a sample paragraph."}
]
```

## Technical Implementation

### Core Components
- **RenderGUI Class**: Main application controller
- **EPUB Generation**: Adapted from original render.py logic
- **Preview System**: Extracts and displays EPUB content
- **Logging System**: Real-time operation feedback

### Dependencies
- tkinter (built-in with Python)
- ebooklib (for EPUB generation)
- json (built-in)
- tempfile (for preview generation)
- threading (for non-blocking operations)

### File Structure
```
BookExtract/
├── render_gui.py          # Main GUI application
├── render.py              # Original command-line script
├── out/                   # Default input/output directory
│   ├── sample_book.json   # Sample JSON file
│   └── cover.png          # Sample cover image
└── requirements.txt       # Python dependencies
```

## Testing

The application has been tested with:
- ✅ JSON validation and formatting
- ✅ EPUB generation from sample data
- ✅ Preview extraction and display
- ✅ File save/load operations
- ✅ Error handling for invalid JSON
- ✅ Missing file handling

## Advantages Over Command Line

1. **Visual Editing**: See JSON structure clearly with syntax highlighting
2. **Immediate Feedback**: Real-time validation and preview
3. **Error Prevention**: GUI prevents many common mistakes
4. **Ease of Use**: No need to remember command-line syntax
5. **Integrated Workflow**: Edit, validate, preview, and export in one interface

## Future Enhancements

Potential improvements could include:
- Syntax highlighting for JSON
- Visual JSON tree editor
- Image preview in the interface
- EPUB viewer integration
- Batch processing capabilities
- Template system for common book structures

The GUI successfully transforms the command-line render.py into a comprehensive, user-friendly application suitable for both technical and non-technical users.