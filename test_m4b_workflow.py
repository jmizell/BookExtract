#!/usr/bin/env python3
"""
Test script for the intermediate to M4B workflow.

This script creates a sample intermediate format file and tests the conversion
to M4B-ready text files to verify the workflow is working correctly.
"""

import json
import tempfile
import os
import subprocess
from pathlib import Path
from book_intermediate import BookIntermediate, BookConverter, BookMetadata, Chapter, ContentSection


def create_test_intermediate():
    """Create a test intermediate format file."""
    # Create sample metadata
    metadata = BookMetadata(
        title="Test Audiobook",
        author="Test Author",
        language="en",
        description="A test book for validating the M4B workflow"
    )
    
    # Create sample chapters
    chapters = []
    
    # Chapter 1
    chapter1_sections = [
        ContentSection(type="chapter_header", content="Introduction"),
        ContentSection(type="paragraph", content="Welcome to this test audiobook. This is the first chapter where we introduce the main concepts."),
        ContentSection(type="paragraph", content="The purpose of this test is to verify that our intermediate format can be successfully converted to M4B audiobook format."),
        ContentSection(type="header", content="Key Features"),
        ContentSection(type="paragraph", content="This test validates several important features of our conversion pipeline."),
        ContentSection(type="bold", content="Remember: This is just a test, but it demonstrates real functionality."),
    ]
    
    chapter1 = Chapter(
        number=1,
        title="Introduction",
        sections=chapter1_sections
    )
    chapters.append(chapter1)
    
    # Chapter 2
    chapter2_sections = [
        ContentSection(type="chapter_header", content="Technical Details"),
        ContentSection(type="paragraph", content="In this chapter, we explore the technical aspects of the conversion process."),
        ContentSection(type="sub_header", content="Text Processing"),
        ContentSection(type="paragraph", content="The system automatically cleans and optimizes text for text-to-speech processing."),
        ContentSection(type="block_indent", content="As the documentation states: 'Quality text processing is essential for good audio output.'"),
        ContentSection(type="page_division"),
        ContentSection(type="paragraph", content="After the page break, we continue with more technical details."),
        ContentSection(type="image", caption="Workflow diagram showing the conversion process"),
    ]
    
    chapter2 = Chapter(
        number=2,
        title="Technical Details",
        sections=chapter2_sections
    )
    chapters.append(chapter2)
    
    # Chapter 3
    chapter3_sections = [
        ContentSection(type="chapter_header", content="Conclusion"),
        ContentSection(type="paragraph", content="This concludes our test audiobook. We have demonstrated the conversion from intermediate format to M4B-ready text files."),
        ContentSection(type="paragraph", content="The next step would be to use text-to-speech software to generate audio files and combine them into an M4B audiobook."),
        ContentSection(type="bold", content="Thank you for testing the BookExtract M4B workflow!"),
    ]
    
    chapter3 = Chapter(
        number=3,
        title="Conclusion",
        sections=chapter3_sections
    )
    chapters.append(chapter3)
    
    # Create the intermediate representation
    intermediate = BookIntermediate(metadata=metadata, chapters=chapters)
    
    return intermediate


def test_intermediate_to_text_conversion():
    """Test the conversion from intermediate format to M4B-ready text files."""
    print("Testing intermediate to M4B text conversion...")
    
    # Create test intermediate
    intermediate = create_test_intermediate()
    
    # Create temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Save intermediate file
        intermediate_file = temp_path / "test_book.json"
        intermediate.save_to_file(intermediate_file)
        print(f"✓ Created test intermediate file: {intermediate_file}")
        
        # Test the conversion using intermediate_to_m4b.py
        output_dir = temp_path / "m4b_output"
        
        try:
            result = subprocess.run([
                "python3", "intermediate_to_m4b.py",
                str(intermediate_file),
                "-o", str(output_dir)
            ], capture_output=True, text=True, check=True)
            
            print("✓ intermediate_to_m4b.py executed successfully")
            print(f"Output: {result.stdout}")
            
            # Check that files were created
            text_files = list(output_dir.glob("*.txt"))
            metadata_file = output_dir / "book_info.json"
            
            print(f"✓ Created {len(text_files)} text files:")
            for txt_file in sorted(text_files):
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    word_count = len(content.split())
                    print(f"  - {txt_file.name}: {word_count} words")
            
            if metadata_file.exists():
                print(f"✓ Created metadata file: {metadata_file.name}")
                
                # Validate metadata
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    print(f"  Title: {metadata['metadata']['title']}")
                    print(f"  Author: {metadata['metadata']['author']}")
                    print(f"  Chapters: {metadata['total_chapters']}")
            else:
                print("✗ Metadata file not created")
                return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ intermediate_to_m4b.py failed: {e}")
            print(f"Error output: {e.stderr}")
            return False


def test_intermediate_validation():
    """Test the intermediate format validation."""
    print("\nTesting intermediate format validation...")
    
    intermediate = create_test_intermediate()
    
    # Test basic properties
    assert intermediate.metadata.title == "Test Audiobook"
    assert intermediate.metadata.author == "Test Author"
    assert intermediate.get_chapter_count() == 3
    
    total_words = intermediate.get_total_word_count()
    print(f"✓ Book has {intermediate.get_chapter_count()} chapters and {total_words} words")
    
    # Test chapter properties
    for i, chapter in enumerate(intermediate.chapters, 1):
        word_count = chapter.get_word_count()
        print(f"✓ Chapter {i}: '{chapter.title}' has {word_count} words")
    
    return True


def test_text_cleaning():
    """Test the text cleaning functionality."""
    print("\nTesting text cleaning for TTS...")
    
    # Import the cleaning function
    from intermediate_to_m4b import clean_text_for_tts
    
    test_cases = [
        ("Hello world", "Hello world."),
        ("This is a test...", "This is a test..."),
        ("Text with regular quotes", "Text with regular quotes."),
        ("Text with apostrophes", "Text with apostrophes."),
        ("Multiple   spaces", "Multiple spaces."),
        ("Text--with--dashes", "Text -- with -- dashes."),
        ("Text with HTML <b>tags</b>", "Text with HTML tags."),
        ("Already ends.", "Already ends."),
        ("Question?", "Question?"),
        ("Exclamation!", "Exclamation!"),
    ]
    
    for input_text, expected in test_cases:
        result = clean_text_for_tts(input_text)
        if result == expected:
            print(f"✓ '{input_text}' → '{result}'")
        else:
            print(f"✗ '{input_text}' → '{result}' (expected '{expected}')")
            return False
    
    return True


def main():
    """Run all tests."""
    print("BookExtract M4B Workflow Test Suite")
    print("=" * 50)
    
    try:
        # Test intermediate format validation
        if not test_intermediate_validation():
            print("✗ Intermediate validation test failed")
            return 1
        
        # Test text cleaning
        if not test_text_cleaning():
            print("✗ Text cleaning test failed")
            return 1
        
        # Test conversion to M4B text files
        if not test_intermediate_to_text_conversion():
            print("✗ Intermediate to M4B conversion test failed")
            return 1
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! M4B workflow is working correctly.")
        print("\nNext steps:")
        print("1. Create an intermediate format file using render_book.py")
        print("2. Run: ./intermediate_to_m4b.sh your_book.json")
        print("3. Enjoy your audiobook!")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())