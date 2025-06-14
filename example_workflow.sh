#!/bin/bash

# Example workflow demonstrating the complete BookExtract pipeline
# This script shows how to go from intermediate format to M4B audiobook

echo "=== BookExtract Complete Workflow Example ==="
echo ""

# Check if we have an intermediate file to work with
if [ ! -f "test_book_intermediate.json" ]; then
    echo "Creating a test intermediate format file for demonstration..."
    python3 -c "
from book_intermediate import BookIntermediate, BookMetadata, Chapter, ContentSection

# Create sample metadata
metadata = BookMetadata(
    title='Example Book',
    author='Example Author',
    language='en',
    description='A test book for demonstrating the BookExtract workflow'
)

# Create sample chapters
chapters = []

# Chapter 1
chapter1_sections = [
    ContentSection(type='chapter_header', content='Introduction'),
    ContentSection(type='paragraph', content='Welcome to this example book. This demonstrates the BookExtract workflow from intermediate format to M4B audiobook.'),
    ContentSection(type='paragraph', content='The intermediate format provides a unified way to represent book content that can be converted to various output formats.'),
    ContentSection(type='header', content='Key Benefits'),
    ContentSection(type='paragraph', content='Using the intermediate format allows for better text processing and more consistent results across different output formats.'),
]

chapter1 = Chapter(number=1, title='Introduction', sections=chapter1_sections)
chapters.append(chapter1)

# Chapter 2
chapter2_sections = [
    ContentSection(type='chapter_header', content='Getting Started'),
    ContentSection(type='paragraph', content='This chapter explains how to use the new intermediate-to-M4B workflow.'),
    ContentSection(type='sub_header', content='Prerequisites'),
    ContentSection(type='paragraph', content='You will need Kokoro TTS and ffmpeg installed on your system.'),
    ContentSection(type='bold', content='Important: Make sure all dependencies are properly installed before proceeding.'),
    ContentSection(type='block_indent', content='The system will automatically validate your setup and provide helpful error messages if anything is missing.'),
]

chapter2 = Chapter(number=2, title='Getting Started', sections=chapter2_sections)
chapters.append(chapter2)

# Create the intermediate representation
intermediate = BookIntermediate(metadata=metadata, chapters=chapters)

# Save to file
intermediate.save_to_file('test_book_intermediate.json')
print('Test intermediate file created: test_book_intermediate.json')
"
fi

echo ""
echo "Step 1: Intermediate format file ready - test_book_intermediate.json"
echo "Step 2: Converting intermediate format to M4B audiobook..."
echo ""

# Convert intermediate format to M4B audiobook
./intermediate_to_m4b.sh test_book_intermediate.json "Example_Audiobook"

echo ""
echo "=== Workflow Complete ==="
echo ""
echo "Files created:"
ls -la *.json *.m4b 2>/dev/null || echo "No output files found"

echo ""
echo "To use with your own books:"
echo "1. Create an intermediate format file using render_book.py"
echo "2. Run: ./intermediate_to_m4b.sh your_book_intermediate.json"
echo "3. Enjoy your audiobook!"
echo ""
echo "Alternative workflows:"
echo "- From EPUB: ./epub_to_m4b.sh your_book.epub"
echo "- From section array: python3 book_intermediate.py --convert-from-sections sections.json && ./intermediate_to_m4b.sh book_intermediate.json"