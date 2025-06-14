#!/usr/bin/env python3
"""
Test script for the intermediate representation system.

This script demonstrates the conversion between different formats and validates
that the intermediate representation works correctly.
"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookextract import BookIntermediate, BookConverter, BookMetadata, Chapter, ContentSection


def create_sample_section_array():
    """Create a sample section array in render_gui format."""
    return [
        {"type": "title", "content": "The Great Adventure"},
        {"type": "author", "content": "Jane Doe"},
        {"type": "cover", "image": "cover.png"},
        {"type": "chapter_header", "content": "1"},
        {"type": "paragraph", "content": "It was a dark and stormy night when our adventure began."},
        {"type": "paragraph", "content": "The wind howled through the trees as Sarah stepped out into the unknown."},
        {"type": "header", "content": "The Journey Begins"},
        {"type": "paragraph", "content": "With determination in her heart, she took the first step."},
        {"type": "chapter_header", "content": "2"},
        {"type": "paragraph", "content": "The next morning brought new challenges and opportunities."},
        {"type": "bold", "content": "Remember: courage is not the absence of fear, but action in spite of it."},
        {"type": "block_indent", "content": "As the old saying goes, 'The journey of a thousand miles begins with a single step.'"},
        {"type": "page_division"},
        {"type": "paragraph", "content": "And so our story continues..."}
    ]


def create_sample_epub_extractor_format():
    """Create a sample book_info.json in epub_extractor format."""
    return {
        "metadata": {
            "title": "The Great Adventure",
            "author": "Jane Doe",
            "language": "en",
            "identifier": "test-book-123"
        },
        "chapters": [
            {
                "number": 1,
                "title": "Chapter 1",
                "filename": "01_chapter_1.txt",
                "content": "It was a dark and stormy night when our adventure began. The wind howled through the trees as Sarah stepped out into the unknown.\n\nThe Journey Begins\n\nWith determination in her heart, she took the first step."
            },
            {
                "number": 2,
                "title": "Chapter 2", 
                "filename": "02_chapter_2.txt",
                "content": "The next morning brought new challenges and opportunities. Remember: courage is not the absence of fear, but action in spite of it.\n\nAs the old saying goes, 'The journey of a thousand miles begins with a single step.'\n\nAnd so our story continues..."
            }
        ],
        "total_chapters": 2
    }


def test_section_array_conversion():
    """Test conversion from section array to intermediate and back."""
    print("Testing section array conversion...")
    
    # Create sample data
    sections = create_sample_section_array()
    
    # Convert to intermediate
    intermediate = BookConverter.from_section_array(sections)
    
    # Validate intermediate format
    assert intermediate.metadata.title == "The Great Adventure"
    assert intermediate.metadata.author == "Jane Doe"
    assert intermediate.metadata.cover_image == "cover.png"
    assert intermediate.get_chapter_count() == 2
    
    print(f"✓ Converted to intermediate: {intermediate.get_chapter_count()} chapters, {intermediate.get_total_word_count()} words")
    
    # Convert back to section array
    sections_back = BookConverter.to_section_array(intermediate)
    
    # Validate round-trip (basic checks)
    title_sections = [s for s in sections_back if s["type"] == "title"]
    author_sections = [s for s in sections_back if s["type"] == "author"]
    chapter_sections = [s for s in sections_back if s["type"] == "chapter_header"]
    
    assert len(title_sections) == 1
    assert title_sections[0]["content"] == "The Great Adventure"
    assert len(author_sections) == 1
    assert author_sections[0]["content"] == "Jane Doe"
    assert len(chapter_sections) == 2
    
    print("✓ Round-trip conversion successful")
    return intermediate


def test_epub_extractor_conversion():
    """Test conversion from epub_extractor format to intermediate."""
    print("\nTesting epub_extractor format conversion...")
    
    # Create sample data
    book_info = create_sample_epub_extractor_format()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(book_info, f, indent=2)
        temp_file = f.name
    
    try:
        # Convert to intermediate
        intermediate = BookConverter.from_epub_extractor(temp_file)
        
        # Validate
        assert intermediate.metadata.title == "The Great Adventure"
        assert intermediate.metadata.author == "Jane Doe"
        assert intermediate.get_chapter_count() == 2
        
        print(f"✓ Converted from epub_extractor: {intermediate.get_chapter_count()} chapters, {intermediate.get_total_word_count()} words")
        
        # Convert back to epub_extractor format
        book_info_back = BookConverter.to_epub_extractor_format(intermediate)
        
        # Validate round-trip
        assert book_info_back["metadata"]["title"] == "The Great Adventure"
        assert book_info_back["metadata"]["author"] == "Jane Doe"
        assert book_info_back["total_chapters"] == 2
        
        print("✓ Round-trip conversion successful")
        return intermediate
        
    finally:
        os.unlink(temp_file)


def test_file_operations():
    """Test saving and loading intermediate files."""
    print("\nTesting file operations...")
    
    # Create sample intermediate
    sections = create_sample_section_array()
    intermediate = BookConverter.from_section_array(sections)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Save intermediate
        intermediate.save_to_file(temp_file)
        print(f"✓ Saved intermediate to: {temp_file}")
        
        # Load intermediate
        loaded_intermediate = BookIntermediate.load_from_file(temp_file)
        
        # Validate
        assert loaded_intermediate.metadata.title == intermediate.metadata.title
        assert loaded_intermediate.metadata.author == intermediate.metadata.author
        assert loaded_intermediate.get_chapter_count() == intermediate.get_chapter_count()
        assert loaded_intermediate.get_total_word_count() == intermediate.get_total_word_count()
        
        print("✓ Load/save round-trip successful")
        
    finally:
        os.unlink(temp_file)


def test_content_analysis():
    """Test content analysis features."""
    print("\nTesting content analysis...")
    
    sections = create_sample_section_array()
    intermediate = BookConverter.from_section_array(sections)
    
    # Test book-level analysis
    total_chapters = intermediate.get_chapter_count()
    total_words = intermediate.get_total_word_count()
    
    print(f"✓ Book analysis: {total_chapters} chapters, {total_words} words")
    
    # Test chapter-level analysis
    for chapter in intermediate.chapters:
        word_count = chapter.get_word_count()
        text_content = chapter.get_text_content()
        print(f"✓ Chapter {chapter.number}: {word_count} words, {len(text_content)} characters")


def test_format_compatibility():
    """Test compatibility between different formats."""
    print("\nTesting format compatibility...")
    
    # Start with section array
    sections = create_sample_section_array()
    intermediate1 = BookConverter.from_section_array(sections)
    
    # Convert to epub_extractor format and back
    epub_format = BookConverter.to_epub_extractor_format(intermediate1)
    
    # Save and reload epub format
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(epub_format, f, indent=2)
        temp_file = f.name
    
    try:
        intermediate2 = BookConverter.from_epub_extractor(temp_file)
        
        # Compare key attributes
        assert intermediate1.metadata.title == intermediate2.metadata.title
        assert intermediate1.metadata.author == intermediate2.metadata.author
        assert intermediate1.get_chapter_count() == intermediate2.get_chapter_count()
        
        print("✓ Format compatibility verified")
        
    finally:
        os.unlink(temp_file)


def main():
    """Run all tests."""
    print("BookExtract Intermediate Representation Test Suite")
    print("=" * 50)
    
    try:
        # Run tests
        test_section_array_conversion()
        test_epub_extractor_conversion()
        test_file_operations()
        test_content_analysis()
        test_format_compatibility()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! Intermediate representation is working correctly.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())