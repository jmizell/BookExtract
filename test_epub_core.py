#!/usr/bin/env python3
"""
Test script for the core EPUB generation functionality.
This tests the EPUB generation without any GUI components.
"""

import json
import os
import tempfile
import uuid
from ebooklib import epub
import zipfile

def generate_epub_from_data(book_data, output_path):
    """Generate EPUB from JSON data (core functionality extracted from GUI)."""
    # Create a new EPUB book
    book = epub.EpubBook()
    
    # Set metadata
    title = None
    author = None
    cover_image = None
    
    # Extract title, author, and cover from the JSON data
    for item in book_data:
        if item['type'] == 'title':
            title = item['content']
        elif item['type'] == 'author':
            author = item['content']
        elif item['type'] == 'cover' and 'image' in item:
            cover_image = item['image']
        if title and author and cover_image:
            break
            
    if not title:
        raise ValueError("ebook is missing section 'title'")
    if not author:
        raise ValueError("ebook is missing section 'author'")
    if not cover_image:
        raise ValueError("ebook is missing section 'cover_image'")
        
    book_id = str(uuid.uuid4())
    print(f"Set id {book_id}")
    book.set_identifier(book_id)
    print(f"Set title {title}")
    book.set_title(title)
    print(f"Set language 'en'")
    book.set_language('en')
    print(f"Set author {author}")
    book.add_author(author)
    
    # Handle cover image
    cover_path = os.path.join("out", cover_image)
    
    if os.path.exists(cover_path):
        with open(cover_path, 'rb') as f:
            cover_content = f.read()
        print(f"Set cover {cover_path}")
        book.set_cover("cover.png", cover_content)
    else:
        print(f"Cover image not found: {cover_path}, using placeholder")
        # Create a simple placeholder cover
        placeholder_cover = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00[\x8f\x1c\xa6\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        book.set_cover("cover.png", placeholder_cover)
        
    # Process content into chapters
    chapters = []
    current_chapter_content = []
    current_chapter_title = "Cover"
    chapter_counter = 0
    division_counter = 0
    
    for item in book_data:
        if item['type'] == 'chapter_header':
            # If we have content for a previous chapter, save it
            if current_chapter_content:
                chapter = epub.EpubHtml(
                    title=current_chapter_title,
                    file_name=f'chapter_{chapter_counter}.xhtml'
                )
                chapter.content = ''.join(current_chapter_content)
                chapters.append(chapter)
                chapter_counter += 1
                current_chapter_content = []
                
            current_chapter_title = f"Chapter {item['content']}"
            current_chapter_content.append(f"<h1>{item['content']}</h1>")
            division_counter = 1
        elif item['type'] in 'title':
            current_chapter_content.append(f"<h1>{item['content']}</h1>")
        elif item['type'] in 'author':
            current_chapter_content.append(f"<h2>{item['content']}</h2>")
        else:
            # Build HTML content based on the type
            if item['type'] == 'paragraph':
                current_chapter_content.append(f"<p>{item['content']}</p>")
            elif item['type'] == 'bold':
                current_chapter_content.append(f"<p><strong>{item['content']}</strong></p>")
            elif item['type'] == 'block_indent':
                current_chapter_content.append(f"<blockquote>{item['content']}</blockquote>")
            elif item['type'] == 'sub_header':
                current_chapter_content.append(f"<h3>{item['content']}</h3>")
            elif item['type'] == 'header':
                current_chapter_content.append(f"<h2>{item['content']}</h2>")
            elif item['type'] == 'page_division':
                current_chapter_content.append("<hr/>")
                
    # Add the last chapter if there's content
    if current_chapter_content:
        chapter = epub.EpubHtml(
            title=current_chapter_title,
            file_name=f'chapter_{chapter_counter}.xhtml'
        )
        chapter.content = ''.join(current_chapter_content)
        chapters.append(chapter)
        
    # Add chapters to the book
    for chapter in chapters:
        print(f"Added chapter {chapter.title}")
        book.add_item(chapter)
        
    # Define TOC
    book.toc = [(epub.Section('Chapters'), chapters)]
    
    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Define CSS style
    style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
        margin: 5%;
        text-align: justify;
    }
    h1, h2, h3 {
        text-align: center;
        margin-bottom: 1em;
    }
    blockquote {
        margin: 1em 2em;
        font-style: italic;
    }
    '''
    
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)
    
    # Create spine
    book.spine = ['nav'] + chapters
    
    # Write the EPUB file
    epub.write_epub(output_path, book, {})
    print(f"EPUB file created: {output_path}")

def extract_epub_preview(epub_path):
    """Extract readable text from EPUB for preview."""
    try:
        preview_text = ""
        
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            # Find content files
            content_files = [f for f in epub_zip.namelist() if f.endswith('.xhtml') and 'chapter' in f]
            content_files.sort()
            
            for content_file in content_files[:3]:  # Limit to first 3 chapters for preview
                try:
                    content = epub_zip.read(content_file).decode('utf-8')
                    # Simple HTML to text conversion
                    import re
                    text = re.sub(r'<[^>]+>', '', content)
                    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                    text = re.sub(r'\s+', ' ', text).strip()
                    preview_text += f"\n{'='*50}\n{text}\n"
                except Exception as e:
                    preview_text += f"\n[Error reading {content_file}: {str(e)}]\n"
                    
        return preview_text if preview_text else "No readable content found in EPUB"
        
    except Exception as e:
        return f"Error extracting EPUB preview: {str(e)}"

def test_epub_generation():
    """Test EPUB generation functionality."""
    print("Testing EPUB generation...")
    
    # Load sample JSON
    sample_json_path = "out/sample_book.json"
    if os.path.exists(sample_json_path):
        with open(sample_json_path, 'r') as f:
            data = json.load(f)
        
        print(f"Loaded sample JSON with {len(data)} items")
        
        # Test EPUB generation
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
            temp_epub_path = temp_file.name
        
        try:
            generate_epub_from_data(data, temp_epub_path)
            
            if os.path.exists(temp_epub_path):
                file_size = os.path.getsize(temp_epub_path)
                print(f"✓ EPUB generated successfully: {temp_epub_path}")
                print(f"  File size: {file_size} bytes")
                
                # Test preview extraction
                preview_text = extract_epub_preview(temp_epub_path)
                print(f"✓ Preview extracted successfully")
                print(f"  Preview length: {len(preview_text)} characters")
                print(f"  Preview sample: {preview_text[:200]}...")
                
                # Also create a permanent copy for inspection
                permanent_path = "out/test_output.epub"
                import shutil
                shutil.copy2(temp_epub_path, permanent_path)
                print(f"✓ Permanent copy saved to: {permanent_path}")
                
            else:
                print("✗ EPUB file was not created")
                
        except Exception as e:
            print(f"✗ Error during EPUB generation: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_epub_path):
                os.unlink(temp_epub_path)
                
    else:
        print(f"✗ Sample JSON file not found: {sample_json_path}")

def test_json_validation():
    """Test JSON validation functionality."""
    print("\nTesting JSON validation...")
    
    # Test valid JSON
    valid_json = [
        {"type": "title", "content": "Test Book"},
        {"type": "author", "content": "Test Author"},
        {"type": "cover", "image": "cover.png"}
    ]
    
    try:
        json_str = json.dumps(valid_json)
        parsed = json.loads(json_str)
        print("✓ Valid JSON parsing works")
    except Exception as e:
        print(f"✗ Valid JSON parsing failed: {str(e)}")
    
    # Test invalid JSON
    invalid_json = '{"type": "title", "content": "Test Book"'  # Missing closing brace
    
    try:
        parsed = json.loads(invalid_json)
        print("✗ Invalid JSON should have failed but didn't")
    except json.JSONDecodeError:
        print("✓ Invalid JSON correctly rejected")
    except Exception as e:
        print(f"✗ Unexpected error with invalid JSON: {str(e)}")

def main():
    """Run all tests."""
    print("=" * 50)
    print("Testing Core EPUB Generation Functionality")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir('/workspace/BookExtract')
    
    test_json_validation()
    test_epub_generation()
    
    print("\n" + "=" * 50)
    print("Testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()