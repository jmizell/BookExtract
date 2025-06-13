# Book Intermediate Representation

This document describes the intermediate representation format that bridges the gap between different book processing pipelines in BookExtract.

## Overview

The intermediate representation provides a unified format that can be used by both EPUB and M4B generation pipelines. It standardizes book content structure while preserving all necessary information for different output formats.

## Benefits

1. **Unified Format**: Single format that works with both EPUB and audiobook generation
2. **Rich Metadata**: Comprehensive book metadata including title, author, language, etc.
3. **Structured Content**: Hierarchical organization with chapters and typed content sections
4. **Extensible**: Easy to add new content types and metadata fields
5. **Backward Compatible**: Can convert to/from existing formats

## Format Structure

### BookIntermediate

The top-level structure contains:

```json
{
  "metadata": {
    "title": "Book Title",
    "author": "Author Name",
    "language": "en",
    "identifier": "uuid-string",
    "publisher": "Publisher Name",
    "description": "Book description",
    "cover_image": "cover.png",
    "creation_date": "2024-01-01T00:00:00"
  },
  "chapters": [
    {
      "number": 1,
      "title": "Chapter Title",
      "filename": "01_chapter.txt",
      "sections": [
        {
          "type": "chapter_header",
          "content": "Chapter 1"
        },
        {
          "type": "paragraph",
          "content": "Chapter content..."
        }
      ],
      "word_count": 1500
    }
  ],
  "total_chapters": 10,
  "total_word_count": 15000,
  "format_version": "1.0"
}
```

### Content Section Types

The intermediate format supports various content types:

- **title**: Book title
- **author**: Author name
- **cover**: Cover image reference
- **chapter_header**: Chapter title/number
- **paragraph**: Regular text paragraph
- **header**: Section header (h2)
- **sub_header**: Subsection header (h3)
- **bold**: Bold/emphasized text
- **block_indent**: Indented block quote
- **image**: Image with optional caption
- **page_division**: Page break marker

## Usage Examples

### Converting from EPUB Extractor Format

```python
from book_intermediate import BookConverter

# Convert from epub_extractor output
intermediate = BookConverter.from_epub_extractor("book_info.json")

# Save as intermediate format
intermediate.save_to_file("book_intermediate.json")
```

### Converting from Section Array Format

```python
import json
from book_intermediate import BookConverter

# Load section array (render_gui format)
with open("book_sections.json", 'r') as f:
    sections = json.load(f)

# Convert to intermediate
intermediate = BookConverter.from_section_array(sections)

# Save intermediate format
intermediate.save_to_file("book_intermediate.json")
```

### Converting Back to Section Array

```python
from book_intermediate import BookIntermediate, BookConverter

# Load intermediate format
intermediate = BookIntermediate.load_from_file("book_intermediate.json")

# Convert to section array for render_gui
sections = BookConverter.to_section_array(intermediate)

# Save as JSON
with open("book_sections.json", 'w') as f:
    json.dump(sections, f, indent=2)
```

## Command Line Tools

### epub_extractor.py

Extract from EPUB and generate intermediate format:

```bash
python epub_extractor.py book.epub -o output_dir --intermediate
```

This creates:
- `output_dir/book_info.json` (legacy format)
- `output_dir/book_intermediate.json` (new intermediate format)
- Individual chapter text files

### intermediate_to_m4b.py

Convert intermediate format to M4B-ready text files:

```bash
python intermediate_to_m4b.py book_intermediate.json -o m4b_ready/
```

This creates:
- Individual text files optimized for TTS
- `book_info.json` for backward compatibility

### book_intermediate.py

Direct conversion between formats:

```bash
# Convert from epub_extractor format
python book_intermediate.py --convert-from-epub book_info.json -o intermediate.json

# Convert from section array format
python book_intermediate.py --convert-from-sections sections.json -o intermediate.json

# Convert intermediate back to section array
python book_intermediate.py --convert-from-sections sections.json --to-sections -o sections_out.json
```

## Integration with Existing Tools

### EPUB to M4B Pipeline

The `epub_to_m4b.sh` script now automatically uses the intermediate format when available:

```bash
./epub_to_m4b.sh book.epub
```

The script will:
1. Extract EPUB content using `epub_extractor.py --intermediate`
2. Use `intermediate_to_m4b.py` to generate optimized text files
3. Process with TTS and create M4B audiobook

### Render GUI

The render GUI now supports:
- Opening intermediate files: **File → Open Intermediate...**
- Saving as intermediate: **File → Save Intermediate As...**
- Automatic conversion between formats

## Migration Guide

### From Legacy epub_extractor Output

If you have existing `book_info.json` files:

```python
from book_intermediate import BookConverter

# Convert legacy format
intermediate = BookConverter.from_epub_extractor("book_info.json")

# Save as intermediate
intermediate.save_to_file("book_intermediate.json")

# Continue using with new tools
```

### From Section Array Format

If you have existing section array JSON files:

```python
import json
from book_intermediate import BookConverter

with open("sections.json", 'r') as f:
    sections = json.load(f)

intermediate = BookConverter.from_section_array(sections)
intermediate.save_to_file("book_intermediate.json")
```

## Advanced Features

### Content Analysis

The intermediate format provides built-in analysis:

```python
intermediate = BookIntermediate.load_from_file("book.json")

print(f"Total chapters: {intermediate.get_chapter_count()}")
print(f"Total words: {intermediate.get_total_word_count()}")

for chapter in intermediate.chapters:
    print(f"Chapter {chapter.number}: {chapter.get_word_count()} words")
```

### Custom Content Types

You can extend the format with custom content types:

```python
from book_intermediate import ContentSection

# Custom content section
custom_section = ContentSection(
    type="custom_callout",
    content="Important note",
    source="page_42"
)
```

### Metadata Enhancement

Rich metadata support:

```python
from book_intermediate import BookMetadata

metadata = BookMetadata(
    title="My Book",
    author="Author Name",
    language="en",
    publisher="My Publisher",
    description="A great book about...",
    cover_image="cover.png"
)
```

## Best Practices

1. **Always validate**: Use the conversion functions to ensure format compatibility
2. **Preserve metadata**: Include as much metadata as possible for better output quality
3. **Structure content**: Use appropriate content types for better formatting
4. **Test conversions**: Verify that round-trip conversions preserve your content
5. **Version control**: The format includes a version field for future compatibility

## Troubleshooting

### Common Issues

1. **Missing required fields**: Ensure title and author are present
2. **Image paths**: Use relative paths from the JSON file location
3. **Content encoding**: Always use UTF-8 encoding for text files
4. **Large files**: For very large books, consider splitting into multiple files

### Validation

```python
try:
    intermediate = BookIntermediate.load_from_file("book.json")
    print("✓ Valid intermediate format")
except Exception as e:
    print(f"✗ Invalid format: {e}")
```

## Future Enhancements

Planned improvements:
- Support for more content types (tables, footnotes, etc.)
- Enhanced image handling with automatic format conversion
- Integration with more TTS engines
- Support for multiple languages in a single book
- Advanced chapter organization (parts, sections)