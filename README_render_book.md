# Book Renderer Tool (render_book.py)

A GUI application for editing book JSON data and previewing content as formatted rich text. This tool focuses on the intermediate format and provides a rich text preview instead of EPUB generation.

## Overview

The Book Renderer Tool is a refactored version of `render_gui.py` that:

- **Focuses on intermediate format editing**: Edit JSON arrays that represent book content
- **Rich text preview**: See your content formatted with proper typography and styling
- **No EPUB dependency**: Removed EPUB generation to focus on content editing and preview
- **Image detection**: Shows image placeholders with file existence status
- **Intermediate format support**: Full integration with the BookExtract intermediate format

## Features

### JSON Editor
- Syntax highlighting and validation
- Auto-formatting with proper indentation
- Undo/redo support (50 levels)
- Auto-stub generation for missing required sections

### Rich Text Preview
- **Styled typography**: Different fonts and sizes for titles, headers, paragraphs
- **Proper spacing**: Automatic spacing between sections and chapters
- **Image placeholders**: Visual indicators for images with file status
- **Chapter organization**: Clear visual separation between chapters
- **Content type indicators**: Visual formatting for different content types

### File Operations
- Open/save JSON files (section array format)
- Open/save intermediate format files
- Automatic format conversion between section arrays and intermediate format
- Default file loading from `out/book.json`

### Content Types Supported

The tool supports all standard BookExtract content types:

- **title**: Book title (large, centered, bold)
- **author**: Author name (medium, centered, italic)
- **cover**: Cover image reference (centered placeholder)
- **chapter_header**: Chapter titles (large, centered, bold)
- **header**: Section headers (medium, bold)
- **sub_header**: Subsection headers (smaller, bold)
- **paragraph**: Regular text content (justified, proper margins)
- **bold**: Emphasized text (bold formatting)
- **block_indent**: Indented quotes (italic, wider margins)
- **image**: Image references with optional captions
- **page_division**: Horizontal rules for section breaks

## Usage

### Starting the Application

```bash
python render_book.py
```

### Basic Workflow

1. **Create or Open Content**:
   - Use `File → New` to create a new document with sample content
   - Use `File → Open JSON...` to open existing section array files
   - Use `File → Open Intermediate...` to open intermediate format files

2. **Edit Content**:
   - Edit the JSON in the left panel
   - Use `Edit → Format JSON` to clean up formatting
   - Use `Edit → Validate JSON` to check for required sections

3. **Preview Content**:
   - The right panel shows a live rich text preview
   - Use `View → Refresh Preview` or F5 to update the preview
   - See your content with proper typography and formatting

4. **Save Work**:
   - Use `File → Save JSON` to save in section array format
   - Use `File → Save Intermediate As...` to save in intermediate format

### Keyboard Shortcuts

- `Ctrl+N`: New document
- `Ctrl+O`: Open JSON file
- `Ctrl+S`: Save current file
- `Ctrl+Shift+S`: Save as new file
- `Ctrl+F`: Format JSON
- `Ctrl+V`: Validate JSON
- `F5`: Refresh preview
- `Ctrl+Q`: Quit application

## Rich Text Formatting

The preview area uses sophisticated text formatting:

### Typography
- **Titles**: Georgia 24pt, bold, centered
- **Authors**: Georgia 16pt, italic, centered
- **Chapter Headers**: Georgia 20pt, bold, centered
- **Section Headers**: Georgia 16pt, bold
- **Subsection Headers**: Georgia 14pt, bold
- **Body Text**: Georgia 11pt, justified
- **Block Quotes**: Georgia 11pt, italic, indented

### Spacing
- Automatic spacing between sections
- Extra spacing around chapter headers
- Proper margins for different content types
- Visual separation with horizontal rules

### Image Handling
- Image placeholders show file paths
- File existence checking with status indicators
- Caption formatting below images
- Centered layout for visual elements

## JSON Format

The tool works with section array format:

```json
[
  {
    "type": "title",
    "content": "Your Book Title"
  },
  {
    "type": "author", 
    "content": "Your Name"
  },
  {
    "type": "cover",
    "image": "cover.png"
  },
  {
    "type": "chapter_header",
    "content": "1"
  },
  {
    "type": "paragraph",
    "content": "Chapter content goes here..."
  },
  {
    "type": "image",
    "image": "chapter1_image.png",
    "caption": "Optional image caption"
  },
  {
    "type": "page_division"
  }
]
```

### Required Sections

The validation system checks for:
- **title**: Book title
- **author**: Author name  
- **cover**: Cover image reference

Missing sections can be auto-generated with placeholder content.

## Intermediate Format Integration

The tool fully supports the BookExtract intermediate format:

### Opening Intermediate Files
- Use `File → Open Intermediate...`
- Automatically converts to section array for editing
- Preserves all metadata and chapter structure

### Saving Intermediate Files
- Use `File → Save Intermediate As...`
- Converts section array to full intermediate format
- Includes metadata, chapter organization, and word counts

### Format Conversion
- Seamless conversion between formats
- Preserves all content and structure
- Maintains compatibility with other BookExtract tools

## Image Management

### Image Paths
- Use relative paths from the JSON file location
- Images are checked for existence during preview
- Status indicators show found/missing files

### Image Display
- Cover images: Centered placeholders with file status
- Content images: Inline placeholders with captions
- File existence checking with clear status messages

### Supported Formats
- Any image format (PNG, JPG, etc.)
- Path validation and existence checking
- Caption support for content images

## Error Handling

### JSON Validation
- Real-time syntax checking
- Clear error messages for invalid JSON
- Auto-formatting to fix common issues

### File Operations
- Graceful handling of missing files
- Clear error messages for file operations
- Automatic backup of unsaved changes

### Image Handling
- Non-blocking image validation
- Clear status indicators for missing images
- Fallback handling for invalid paths

## Integration with BookExtract

### Workflow Integration
- Compatible with `epub_extractor.py` output
- Works with `intermediate_to_m4b.py` input
- Supports the full BookExtract pipeline

### Format Compatibility
- Section array format (render_gui compatible)
- Intermediate format (new unified format)
- Automatic conversion between formats

## Differences from render_gui.py

### Removed Features
- EPUB generation and preview
- EPUB file operations
- Browser integration for EPUB viewing
- EPUB-specific validation

### Enhanced Features
- **Rich text preview**: Much more sophisticated formatting
- **Better typography**: Professional text layout
- **Image status**: Real-time file existence checking
- **Intermediate format**: Full support for new format
- **Simplified interface**: Focus on content editing

### New Features
- **Text tag system**: Rich formatting with proper typography
- **Content type styling**: Different styles for each content type
- **Image placeholders**: Visual representation of images
- **Status indicators**: Clear feedback on file operations

## Troubleshooting

### Common Issues

1. **Images not showing**: Check that image paths are relative to JSON file location
2. **JSON validation errors**: Use Format JSON to fix syntax issues
3. **Missing required sections**: Use Validate JSON to auto-generate stubs
4. **Preview not updating**: Use F5 or Refresh Preview button

### Performance
- Large documents may take a moment to render
- Image checking is done in real-time
- Threading prevents UI blocking during operations

## Future Enhancements

Planned improvements:
- **Actual image preview**: Display actual images instead of placeholders
- **Export options**: Export to various text formats
- **Advanced editing**: Inline editing capabilities
- **Theme support**: Multiple color schemes and fonts
- **Plugin system**: Extensible content type support

## Development

### Testing
Run the test scripts to verify functionality:

```bash
python test_render_book.py          # Basic functionality test
python test_with_images.py          # Image handling test  
python test_intermediate_integration.py  # Intermediate format test
```

### Architecture
- **Main class**: `RenderBookGUI` - Main application window
- **Rich text engine**: Text widget with custom tags for formatting
- **Format conversion**: Integration with `book_intermediate.py`
- **Threading**: Non-blocking preview generation

### Dependencies
- `tkinter`: GUI framework (built into Python)
- `book_intermediate`: BookExtract intermediate format support
- Standard library: `json`, `os`, `pathlib`, `threading`

## License

Same license as the BookExtract project.