#!/bin/bash

# Example workflow demonstrating the complete BookExtract pipeline
# This script shows how to go from EPUB to M4B audiobook

echo "=== BookExtract Complete Workflow Example ==="
echo ""

# Check if we have an EPUB file to work with
if [ ! -f "test_book.epub" ]; then
    echo "Creating a test EPUB file for demonstration..."
    python3 -c "
from ebooklib import epub

# Create a simple test book
book = epub.EpubBook()
book.set_identifier('example-123')
book.set_title('Example Book')
book.set_language('en')
book.add_author('Example Author')

# Add a chapter
c1 = epub.EpubHtml(title='Chapter 1', file_name='chap_01.xhtml')
c1.content = '''<html><body><h1>Chapter 1</h1><p>This is an example chapter for testing the BookExtract workflow.</p></body></html>'''
book.add_item(c1)

book.toc = [c1]
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())
book.spine = ['nav', c1]

epub.write_epub('test_book.epub', book, {})
print('Test EPUB created: test_book.epub')
"
fi

echo ""
echo "Step 1: EPUB file ready - test_book.epub"
echo "Step 2: Converting EPUB to M4B audiobook..."
echo ""

# Convert EPUB to M4B audiobook
./epub_to_m4b.sh test_book.epub "Example_Audiobook"

echo ""
echo "=== Workflow Complete ==="
echo ""
echo "Files created:"
ls -la *.epub *.m4b 2>/dev/null || echo "No output files found"

echo ""
echo "To use with your own books:"
echo "1. Place your EPUB file in this directory"
echo "2. Run: ./epub_to_m4b.sh your_book.epub"
echo "3. Enjoy your audiobook!"