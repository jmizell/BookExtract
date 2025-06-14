#!/usr/bin/env python3
"""
Unit tests for the intermediate_to_m4b module.

Tests text file generation, content cleaning, and metadata creation
for M4B audiobook processing.
"""

import unittest
import tempfile
import os
import sys
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookextract import (
    BookIntermediate, BookConverter, BookMetadata, Chapter, ContentSection,
    create_text_files_from_intermediate, clean_text_for_tts, create_metadata_file,
    process_intermediate_file, process_intermediate_file_object
)


class TestTextCleaning(unittest.TestCase):
    """Test text cleaning functions for TTS processing."""
    
    def test_clean_text_for_tts_basic(self):
        """Test basic text cleaning for TTS."""
        test_cases = [
            ("Hello world!", "Hello world!"),
            ("Text with\nmultiple\nlines", "Text with multiple lines."),
            ("Extra   spaces   here", "Extra spaces here."),
            ("Text with\ttabs", "Text with tabs."),
            ("Mixed\n\n\nlines\tand   spaces", "Mixed lines and spaces."),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = clean_text_for_tts(input_text)
                self.assertEqual(result, expected)
                
    def test_clean_text_for_tts_special_characters(self):
        """Test cleaning of special characters for TTS."""
        test_cases = [
            ('Text with "smart quotes"', 'Text with "smart quotes".'),
            ("Text with 'smart apostrophes'", "Text with 'smart apostrophes'."),
            ("Ellipsis…", "Ellipsis...."),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = clean_text_for_tts(input_text)
                # Check that problematic characters are handled
                self.assertNotIn(""", result)
                self.assertNotIn(""", result)
                self.assertNotIn("…", result)
                
    def test_clean_text_for_tts_empty_input(self):
        """Test cleaning empty or whitespace-only input."""
        test_cases = ["", "   ", "\n\n\n", "\t\t", "   \n\t   "]
        
        for input_text in test_cases:
            with self.subTest(input_text=repr(input_text)):
                result = clean_text_for_tts(input_text)
                self.assertEqual(result, "")
                
    def test_clean_text_for_tts_preserves_structure(self):
        """Test that cleaning preserves important text structure."""
        input_text = "Chapter 1: The Beginning\n\nThis is a paragraph.\n\nThis is another paragraph."
        result = clean_text_for_tts(input_text)
        
        # Should preserve paragraph breaks
        self.assertIn("Chapter 1: The Beginning", result)
        self.assertIn("This is a paragraph.", result)
        self.assertIn("This is another paragraph.", result)


class TestTextFileGeneration(unittest.TestCase):
    """Test text file generation from intermediate format."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample intermediate data
        self.metadata = BookMetadata(
            title="Test Book",
            author="Test Author",
            language="en",
            identifier="test-book-123"
        )
        
        # Create chapters with content
        chapter1 = Chapter(
            number=1, 
            title="First Chapter",
            sections=[
                ContentSection(type="chapter_header", content="1"),
                ContentSection(type="paragraph", content="This is the first paragraph of chapter one."),
                ContentSection(type="paragraph", content="This is the second paragraph."),
                ContentSection(type="header", content="A Section Header"),
                ContentSection(type="paragraph", content="Content under the header."),
            ]
        )
        
        chapter2 = Chapter(
            number=2, 
            title="Second Chapter",
            sections=[
                ContentSection(type="chapter_header", content="2"),
                ContentSection(type="paragraph", content="This is the first paragraph of chapter two."),
                ContentSection(type="bold", content="This is bold text."),
                ContentSection(type="block_indent", content="This is an indented quote."),
            ]
        )
        
        self.intermediate = BookIntermediate(
            metadata=self.metadata,
            chapters=[chapter1, chapter2]
        )
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_create_text_files_from_intermediate(self):
        """Test creating text files from intermediate representation."""
        create_text_files_from_intermediate(self.intermediate, self.temp_dir)
        
        # Check that title file was created
        title_file = self.temp_dir / "00_title.txt"
        self.assertTrue(title_file.exists())
        
        with open(title_file, 'r', encoding='utf-8') as f:
            title_content = f.read()
            
        self.assertIn("Test Book", title_content)
        self.assertIn("Test Author", title_content)
        
        # Check that chapter files were created
        chapter1_file = self.temp_dir / "01_First_Chapter.txt"
        chapter2_file = self.temp_dir / "02_Second_Chapter.txt"
        
        self.assertTrue(chapter1_file.exists())
        self.assertTrue(chapter2_file.exists())
        
        # Check chapter 1 content
        with open(chapter1_file, 'r', encoding='utf-8') as f:
            chapter1_content = f.read()
            
        self.assertIn("Chapter 1: First Chapter", chapter1_content)
        self.assertIn("first paragraph of chapter one", chapter1_content)
        self.assertIn("A Section Header", chapter1_content)
        
        # Check chapter 2 content
        with open(chapter2_file, 'r', encoding='utf-8') as f:
            chapter2_content = f.read()
            
        self.assertIn("Chapter 2: Second Chapter", chapter2_content)
        self.assertIn("first paragraph of chapter two", chapter2_content)
        self.assertIn("bold text", chapter2_content)
        self.assertIn("indented quote", chapter2_content)
        
    def test_filename_sanitization(self):
        """Test that chapter filenames are properly sanitized."""
        # Create chapter with problematic title
        problematic_chapter = Chapter(
            number=3, 
            title="Chapter with / and \\ and : characters",
            sections=[
                ContentSection(type="paragraph", content="Test content.")
            ]
        )
        
        intermediate = BookIntermediate(
            metadata=self.metadata,
            chapters=[problematic_chapter]
        )
        
        create_text_files_from_intermediate(intermediate, self.temp_dir)
        
        # Check that file was created with sanitized name
        files = list(self.temp_dir.glob("03_*.txt"))
        self.assertEqual(len(files), 1)
        
        filename = files[0].name
        # Should not contain problematic characters
        self.assertNotIn("/", filename)
        self.assertNotIn("\\", filename)
        self.assertNotIn(":", filename)
        
    def test_empty_chapters_handling(self):
        """Test handling of chapters with no content."""
        empty_chapter = Chapter(number=1, title="Empty Chapter", sections=[])
        
        intermediate = BookIntermediate(
            metadata=self.metadata,
            chapters=[empty_chapter]
        )
        
        create_text_files_from_intermediate(intermediate, self.temp_dir)
        
        # Should still create file for empty chapter
        chapter_file = self.temp_dir / "01_Empty_Chapter.txt"
        self.assertTrue(chapter_file.exists())
        
        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Should at least have chapter title
        self.assertIn("Chapter 1: Empty Chapter", content)


class TestMetadataGeneration(unittest.TestCase):
    """Test metadata file generation for M4B processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        self.metadata = BookMetadata(
            title="Test Audiobook",
            author="Test Author",
            language="en",
            identifier="test-audiobook-456"
        )
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_create_metadata_file(self):
        """Test creating metadata file for M4B processing."""
        # Create a complete intermediate object
        chapter = Chapter(
            number=1, 
            title="Test Chapter",
            sections=[ContentSection(type="paragraph", content="Test content.")]
        )
        intermediate = BookIntermediate(metadata=self.metadata, chapters=[chapter])
        
        create_metadata_file(intermediate, self.temp_dir)
        
        metadata_file = self.temp_dir / "book_info.json"
        self.assertTrue(metadata_file.exists())
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check that metadata is properly formatted
        self.assertIn("Test Audiobook", content)
        self.assertIn("Test Author", content)
        
    def test_metadata_file_format(self):
        """Test that metadata file has correct format for ffmpeg."""
        # Create a complete intermediate object
        chapter = Chapter(
            number=1, 
            title="Test Chapter",
            sections=[ContentSection(type="paragraph", content="Test content.")]
        )
        intermediate = BookIntermediate(metadata=self.metadata, chapters=[chapter])
        
        create_metadata_file(intermediate, self.temp_dir)
        
        metadata_file = self.temp_dir / "book_info.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            import json
            metadata = json.load(f)
            
        # Should have proper JSON metadata format
        self.assertIn("metadata", metadata)
        self.assertIn("title", metadata["metadata"])
        self.assertIn("author", metadata["metadata"])


class TestIntermediateFileProcessing(unittest.TestCase):
    """Test processing of intermediate files."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample intermediate file
        self.intermediate_data = {
            "metadata": {
                "title": "Test Book for Processing",
                "author": "Processing Author",
                "language": "en",
                "identifier": "process-test-789"
            },
            "chapters": [
                {
                    "number": 1,
                    "title": "Processing Chapter",
                    "sections": [
                        {"type": "paragraph", "content": "This is test content for processing."}
                    ]
                }
            ]
        }
        
        self.intermediate_file = self.temp_dir / "test_intermediate.json"
        with open(self.intermediate_file, 'w', encoding='utf-8') as f:
            json.dump(self.intermediate_data, f, indent=2)
            
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_process_intermediate_file(self):
        """Test processing intermediate file to create text files."""
        output_dir = self.temp_dir / "output"
        
        process_intermediate_file(self.intermediate_file, output_dir)
        
        # Check that output directory was created
        self.assertTrue(output_dir.exists())
        
        # Check that files were created
        title_file = output_dir / "00_title.txt"
        chapter_file = output_dir / "01_Processing_Chapter.txt"
        
        self.assertTrue(title_file.exists())
        self.assertTrue(chapter_file.exists())
        
        # Check content
        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn("Processing Chapter", content)
        self.assertIn("test content for processing", content)
        
    def test_process_intermediate_file_object(self):
        """Test processing intermediate object directly."""
        # Create intermediate object
        metadata = BookMetadata(
            title="Object Test Book",
            author="Object Author",
            language="en"
        )
        
        chapter = Chapter(
            number=1, 
            title="Object Chapter",
            sections=[
                ContentSection(type="paragraph", content="Object test content.")
            ]
        )
        
        intermediate = BookIntermediate(metadata=metadata, chapters=[chapter])
        
        output_dir = self.temp_dir / "object_output"
        
        process_intermediate_file_object(intermediate, output_dir)
        
        # Check that files were created
        self.assertTrue(output_dir.exists())
        
        title_file = output_dir / "00_title.txt"
        chapter_file = output_dir / "01_Object_Chapter.txt"
        
        self.assertTrue(title_file.exists())
        self.assertTrue(chapter_file.exists())
        



class TestErrorHandling(unittest.TestCase):
    """Test error handling in intermediate to M4B processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_invalid_intermediate_file(self):
        """Test handling of invalid intermediate files."""
        # Create invalid JSON file
        invalid_file = self.temp_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json content")
            
        output_dir = self.temp_dir / "output"
        
        # Should handle error gracefully
        with self.assertRaises((json.JSONDecodeError, ValueError, KeyError)):
            process_intermediate_file(invalid_file, output_dir)
            
    def test_missing_intermediate_file(self):
        """Test handling of missing intermediate files."""
        nonexistent_file = self.temp_dir / "nonexistent.json"
        output_dir = self.temp_dir / "output"
        
        # Should handle missing file gracefully
        with self.assertRaises(FileNotFoundError):
            process_intermediate_file(nonexistent_file, output_dir)


if __name__ == '__main__':
    unittest.main()