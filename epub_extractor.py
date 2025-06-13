#!/usr/bin/env python3
"""
EPUB Text Extractor for Audiobook Generation
Extracts text content from EPUB files chapter by chapter for TTS processing.
"""

import os
import sys
import json
import re
from ebooklib import epub
from bs4 import BeautifulSoup
import argparse


def clean_text(text):
    """Clean and normalize text for TTS processing."""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Fix common issues for TTS
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', "'")
    
    # Remove or replace problematic characters for TTS
    text = re.sub(r'[^\w\s\.,!?;:\'"()\-–—]', '', text)
    
    return text


def extract_text_from_html(html_content):
    """Extract clean text from HTML content."""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text and clean it
    text = soup.get_text()
    return clean_text(text)


def extract_epub_content(epub_path, output_dir):
    """Extract content from EPUB file and organize by chapters."""
    
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read EPUB
    book = epub.read_epub(epub_path)
    
    # Extract metadata
    metadata = {
        'title': book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else 'Unknown Title',
        'author': book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else 'Unknown Author',
        'language': book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else 'en',
        'identifier': book.get_metadata('DC', 'identifier')[0][0] if book.get_metadata('DC', 'identifier') else '',
    }
    
    print(f"Processing: {metadata['title']} by {metadata['author']}")
    
    # Create title page content
    title_content = f"{metadata['title']}\n\nBy {metadata['author']}\n\n"
    
    # Write title page
    title_file = os.path.join(output_dir, "00_title.txt")
    with open(title_file, 'w', encoding='utf-8') as f:
        f.write(title_content)
    
    # Extract chapters
    chapters = []
    chapter_num = 1
    
    # Get all items from the book
    for item in book.get_items():
        if item.get_type() == 9 and item.get_name() != 'nav.xhtml':  # Type 9 is document, skip nav
            # Extract text from HTML content
            try:
                content = item.get_content().decode('utf-8')
                text_content = extract_text_from_html(content)
                
                if text_content and len(text_content.strip()) > 50:  # Only include substantial content
                    # Determine chapter title
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for chapter title in h1, h2, or title tags
                    chapter_title = None
                    for tag in ['h1', 'h2', 'title']:
                        title_elem = soup.find(tag)
                        if title_elem:
                            chapter_title = clean_text(title_elem.get_text())
                            break
                    
                    if not chapter_title:
                        chapter_title = f"Chapter {chapter_num}"
                    
                    # Clean up chapter title for filename
                    safe_title = re.sub(r'[^\w\s\-]', '', chapter_title)
                    safe_title = re.sub(r'\s+', '_', safe_title.strip())
                    
                    chapter_info = {
                        'number': chapter_num,
                        'title': chapter_title,
                        'filename': f"{chapter_num:02d}_{safe_title}.txt",
                        'content': text_content
                    }
                    
                    chapters.append(chapter_info)
                    
                    # Write chapter file
                    chapter_file = os.path.join(output_dir, chapter_info['filename'])
                    with open(chapter_file, 'w', encoding='utf-8') as f:
                        f.write(f"{chapter_title}\n\n{text_content}")
                    
                    print(f"Extracted: {chapter_title}")
                    chapter_num += 1
            except Exception as e:
                print(f"Warning: Could not process item {item.get_name()}: {e}")
                continue
    
    # Save metadata and chapter info
    book_info = {
        'metadata': metadata,
        'chapters': chapters,
        'total_chapters': len(chapters)
    }
    
    info_file = os.path.join(output_dir, "book_info.json")
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(book_info, f, indent=2, ensure_ascii=False)
    
    print(f"\nExtracted {len(chapters)} chapters to {output_dir}")
    print(f"Book info saved to {info_file}")
    
    return book_info


def main():
    parser = argparse.ArgumentParser(description='Extract text from EPUB for audiobook generation')
    parser.add_argument('epub_file', help='Path to EPUB file')
    parser.add_argument('-o', '--output', default='epub_extracted', 
                       help='Output directory for extracted text files')
    
    args = parser.parse_args()
    
    try:
        book_info = extract_epub_content(args.epub_file, args.output)
        print(f"\nSuccess! Ready for TTS processing.")
        print(f"Title: {book_info['metadata']['title']}")
        print(f"Author: {book_info['metadata']['author']}")
        print(f"Chapters: {book_info['total_chapters']}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()