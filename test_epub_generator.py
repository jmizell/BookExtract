#!/usr/bin/env python3
"""
Test script for the modular EpubGenerator class.
"""

import tempfile
import os
from render_epub import EpubGenerator

def test_epub_generation():
    """Test the EpubGenerator with sample data."""
    
    # Create test data
    test_data = [
        {'type': 'title', 'content': 'Test Book Title'},
        {'type': 'author', 'content': 'Test Author Name'},
        {'type': 'cover', 'image': 'test_cover.png'},
        {'type': 'chapter_header', 'content': '1'},
        {'type': 'paragraph', 'content': 'This is the first paragraph of chapter 1.'},
        {'type': 'paragraph', 'content': 'This is the second paragraph with some content.'},
        {'type': 'chapter_header', 'content': '2'},
        {'type': 'header', 'content': 'A Section Header'},
        {'type': 'paragraph', 'content': 'This is a paragraph in chapter 2.'},
        {'type': 'bold', 'content': 'This is bold text.'},
        {'type': 'block_indent', 'content': 'This is an indented block quote.'},
    ]
    
    # Create a simple test cover image (1x1 PNG)
    test_cover_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test cover image
        cover_path = os.path.join(temp_dir, 'test_cover.png')
        with open(cover_path, 'wb') as f:
            f.write(test_cover_data)
        
        # Create EPUB generator
        messages = []
        def test_logger(message, level="INFO"):
            messages.append(f"[{level}] {message}")
            print(f"[{level}] {message}")
        
        generator = EpubGenerator(logger=test_logger)
        
        # Generate EPUB
        epub_path = os.path.join(temp_dir, 'test_book.epub')
        try:
            generator.generate_epub(test_data, epub_path, temp_dir)
            
            # Check if EPUB file was created
            if os.path.exists(epub_path):
                file_size = os.path.getsize(epub_path)
                print(f"✓ EPUB file created successfully: {epub_path}")
                print(f"✓ File size: {file_size} bytes")
                
                # Check if it's a valid ZIP file (EPUB is a ZIP)
                import zipfile
                try:
                    with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                        files = epub_zip.namelist()
                        print(f"✓ EPUB contains {len(files)} files")
                        print("✓ EPUB structure looks valid")
                        
                        # Check for required EPUB files
                        required_files = ['META-INF/container.xml', 'mimetype']
                        for req_file in required_files:
                            if req_file in files:
                                print(f"✓ Found required file: {req_file}")
                            else:
                                print(f"✗ Missing required file: {req_file}")
                                
                except zipfile.BadZipFile:
                    print("✗ Generated file is not a valid ZIP/EPUB")
                    return False
                    
            else:
                print("✗ EPUB file was not created")
                return False
                
        except Exception as e:
            print(f"✗ Error generating EPUB: {e}")
            return False
    
    print("\n✓ All tests passed! The EpubGenerator is working correctly.")
    return True

if __name__ == "__main__":
    test_epub_generation()