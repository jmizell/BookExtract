#!/usr/bin/env python3
"""
Extended unit tests for the EpubGenerator class.

Tests edge cases, error handling, and advanced functionality
beyond the basic test already provided.
"""

import unittest
import tempfile
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookextract.epub_generator import EpubGenerator


class TestEpubGeneratorEdgeCases(unittest.TestCase):
    """Test edge cases and error handling for EpubGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = EpubGenerator()
        
        # Create a test cover image
        self.cover_path = os.path.join(self.temp_dir, 'test_cover.png')
        test_cover_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(self.cover_path, 'wb') as f:
            f.write(test_cover_data)
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_empty_content_handling(self):
        """Test handling of empty content."""
        empty_data = []
        
        epub_path = os.path.join(self.temp_dir, 'empty.epub')
        
        # Should handle empty content gracefully
        try:
            self.generator.generate_epub(empty_data, epub_path, self.temp_dir)
            
            # Should still create a valid EPUB structure
            self.assertTrue(os.path.exists(epub_path))
            
            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                files = epub_zip.namelist()
                
                # Should have basic EPUB structure
                self.assertIn('META-INF/container.xml', files)
                self.assertIn('mimetype', files)
                
        except Exception as e:
            # If it raises an exception, it should be a meaningful one
            self.assertIsInstance(e, (ValueError, TypeError))
            
    def test_missing_title_handling(self):
        """Test handling of content without title."""
        data_without_title = [
            {'type': 'author', 'content': 'Test Author'},
            {'type': 'paragraph', 'content': 'Content without title.'},
        ]
        
        epub_path = os.path.join(self.temp_dir, 'no_title.epub')
        
        try:
            self.generator.generate_epub(data_without_title, epub_path, self.temp_dir)
            
            # Should handle missing title gracefully
            self.assertTrue(os.path.exists(epub_path))
            
        except Exception as e:
            # Should provide meaningful error message
            self.assertIn("title", str(e).lower())
            
    def test_missing_author_handling(self):
        """Test handling of content without author."""
        data_without_author = [
            {'type': 'title', 'content': 'Test Book'},
            {'type': 'paragraph', 'content': 'Content without author.'},
        ]
        
        epub_path = os.path.join(self.temp_dir, 'no_author.epub')
        
        try:
            self.generator.generate_epub(data_without_author, epub_path, self.temp_dir)
            
            # Should handle missing author gracefully
            self.assertTrue(os.path.exists(epub_path))
            
        except Exception as e:
            # Should provide meaningful error message
            self.assertIn("author", str(e).lower())
            
    def test_invalid_cover_image_handling(self):
        """Test handling of invalid cover image."""
        data_with_invalid_cover = [
            {'type': 'title', 'content': 'Test Book'},
            {'type': 'author', 'content': 'Test Author'},
            {'type': 'cover', 'image': 'nonexistent_image.png'},
            {'type': 'paragraph', 'content': 'Test content.'},
        ]
        
        epub_path = os.path.join(self.temp_dir, 'invalid_cover.epub')
        
        try:
            self.generator.generate_epub(data_with_invalid_cover, epub_path, self.temp_dir)
            
            # Should handle invalid cover gracefully
            self.assertTrue(os.path.exists(epub_path))
            
        except Exception as e:
            # Should provide meaningful error about cover image
            self.assertTrue(
                "cover" in str(e).lower() or 
                "image" in str(e).lower() or
                "file" in str(e).lower()
            )
            
    def test_special_characters_in_content(self):
        """Test handling of special characters in content."""
        data_with_special_chars = [
            {'type': 'title', 'content': 'Test Book with Special Chars: <>&"\''},
            {'type': 'author', 'content': 'Author with Émojis 📚'},
            {'type': 'cover', 'image': self.cover_path},
            {'type': 'paragraph', 'content': 'Content with HTML <tags> & entities'},
            {'type': 'paragraph', 'content': 'Unicode: café, naïve, résumé'},
        ]
        
        epub_path = os.path.join(self.temp_dir, 'special_chars.epub')
        
        self.generator.generate_epub(data_with_special_chars, epub_path, self.temp_dir)
        
        # Should create valid EPUB
        self.assertTrue(os.path.exists(epub_path))
        
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            # Check that content files exist
            files = epub_zip.namelist()
            content_files = [f for f in files if f.endswith('.xhtml')]
            self.assertGreater(len(content_files), 0)
            
    def test_very_long_content(self):
        """Test handling of very long content."""
        long_paragraph = "This is a very long paragraph. " * 1000
        
        data_with_long_content = [
            {'type': 'title', 'content': 'Test Book with Long Content'},
            {'type': 'author', 'content': 'Test Author'},
            {'type': 'cover', 'image': self.cover_path},
            {'type': 'paragraph', 'content': long_paragraph},
        ]
        
        epub_path = os.path.join(self.temp_dir, 'long_content.epub')
        
        self.generator.generate_epub(data_with_long_content, epub_path, self.temp_dir)
        
        # Should create valid EPUB
        self.assertTrue(os.path.exists(epub_path))
        
        # Check file size is reasonable
        file_size = os.path.getsize(epub_path)
        self.assertGreater(file_size, 1000)  # Should be substantial
        self.assertLess(file_size, 10 * 1024 * 1024)  # But not too large
        
    def test_many_chapters(self):
        """Test handling of many chapters."""
        data_with_many_chapters = [
            {'type': 'title', 'content': 'Book with Many Chapters'},
            {'type': 'author', 'content': 'Test Author'},
            {'type': 'cover', 'image': self.cover_path},
        ]
        
        # Add 50 chapters
        for i in range(1, 51):
            data_with_many_chapters.extend([
                {'type': 'chapter_header', 'content': str(i)},
                {'type': 'paragraph', 'content': f'This is chapter {i} content.'},
            ])
            
        epub_path = os.path.join(self.temp_dir, 'many_chapters.epub')
        
        self.generator.generate_epub(data_with_many_chapters, epub_path, self.temp_dir)
        
        # Should create valid EPUB
        self.assertTrue(os.path.exists(epub_path))
        
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            files = epub_zip.namelist()
            
            # Should have many chapter files
            chapter_files = [f for f in files if 'chapter' in f.lower()]
            self.assertGreater(len(chapter_files), 40)  # Should have most chapters


class TestEpubGeneratorConfiguration(unittest.TestCase):
    """Test configuration and customization of EpubGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test cover image
        self.cover_path = os.path.join(self.temp_dir, 'test_cover.png')
        test_cover_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(self.cover_path, 'wb') as f:
            f.write(test_cover_data)
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_custom_logger(self):
        """Test using custom logger."""
        messages = []
        
        def custom_logger(message, level="INFO"):
            messages.append((level, message))
            
        generator = EpubGenerator(logger=custom_logger)
        
        test_data = [
            {'type': 'title', 'content': 'Test Book'},
            {'type': 'author', 'content': 'Test Author'},
            {'type': 'cover', 'image': self.cover_path},
            {'type': 'paragraph', 'content': 'Test content.'},
        ]
        
        epub_path = os.path.join(self.temp_dir, 'custom_logger.epub')
        
        generator.generate_epub(test_data, epub_path, self.temp_dir)
        
        # Should have logged messages
        self.assertGreater(len(messages), 0)
        
        # Check that different log levels are used
        levels = [msg[0] for msg in messages]
        self.assertIn("INFO", levels)
        
    def test_no_logger(self):
        """Test operation without logger."""
        generator = EpubGenerator(logger=None)
        
        test_data = [
            {'type': 'title', 'content': 'Test Book'},
            {'type': 'author', 'content': 'Test Author'},
            {'type': 'cover', 'image': self.cover_path},
            {'type': 'paragraph', 'content': 'Test content.'},
        ]
        
        epub_path = os.path.join(self.temp_dir, 'no_logger.epub')
        
        # Should work without logger
        generator.generate_epub(test_data, epub_path, self.temp_dir)
        
        self.assertTrue(os.path.exists(epub_path))
        
    def test_custom_metadata(self):
        """Test setting custom metadata."""
        if hasattr(EpubGenerator, 'set_metadata'):
            generator = EpubGenerator()
            
            custom_metadata = {
                'language': 'fr',
                'publisher': 'Test Publisher',
                'date': '2024-01-01',
                'description': 'Test description'
            }
            
            generator.set_metadata(custom_metadata)
            
            test_data = [
                {'type': 'title', 'content': 'Livre de Test'},
                {'type': 'author', 'content': 'Auteur de Test'},
                {'type': 'paragraph', 'content': 'Contenu de test.'},
            ]
            
            epub_path = os.path.join(self.temp_dir, 'custom_metadata.epub')
            
            generator.generate_epub(test_data, epub_path, self.temp_dir)
            
            self.assertTrue(os.path.exists(epub_path))


class TestEpubGeneratorValidation(unittest.TestCase):
    """Test validation functionality of EpubGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = EpubGenerator()
        
        # Create a test cover image
        self.cover_path = os.path.join(self.temp_dir, 'test_cover.png')
        test_cover_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(self.cover_path, 'wb') as f:
            f.write(test_cover_data)
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_validate_epub_structure(self):
        """Test validation of generated EPUB structure."""
        test_data = [
            {'type': 'title', 'content': 'Validation Test Book'},
            {'type': 'author', 'content': 'Test Author'},
            {'type': 'cover', 'image': self.cover_path},
            {'type': 'chapter_header', 'content': '1'},
            {'type': 'paragraph', 'content': 'Test content for validation.'},
        ]
        
        epub_path = os.path.join(self.temp_dir, 'validation_test.epub')
        
        self.generator.generate_epub(test_data, epub_path, self.temp_dir)
        
        # Validate EPUB structure
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            files = epub_zip.namelist()
            
            # Required EPUB files
            required_files = [
                'META-INF/container.xml',
                'mimetype'
            ]
            
            for required_file in required_files:
                self.assertIn(required_file, files)
                
            # Check mimetype content
            mimetype_content = epub_zip.read('mimetype').decode('utf-8')
            self.assertEqual(mimetype_content.strip(), 'application/epub+zip')
            
            # Check container.xml content
            container_content = epub_zip.read('META-INF/container.xml').decode('utf-8')
            self.assertIn('container', container_content)
            self.assertIn('rootfile', container_content)
            
    def test_content_validation(self):
        """Test validation of content structure."""
        if hasattr(self.generator, 'validate_content'):
            # Valid content
            valid_data = [
                {'type': 'title', 'content': 'Valid Book'},
                {'type': 'author', 'content': 'Valid Author'},
                {'type': 'paragraph', 'content': 'Valid content.'},
            ]
            
            is_valid = self.generator.validate_content(valid_data)
            self.assertTrue(is_valid)
            
            # Invalid content
            invalid_data = [
                {'type': 'unknown_type', 'content': 'Invalid content'},
            ]
            
            is_valid = self.generator.validate_content(invalid_data)
            self.assertFalse(is_valid)
            
    def test_output_path_validation(self):
        """Test validation of output path."""
        if hasattr(self.generator, 'validate_output_path'):
            # Valid path
            valid_path = os.path.join(self.temp_dir, 'valid.epub')
            is_valid = self.generator.validate_output_path(valid_path)
            self.assertTrue(is_valid)
            
            # Invalid path (directory doesn't exist)
            invalid_path = '/nonexistent/directory/invalid.epub'
            is_valid = self.generator.validate_output_path(invalid_path)
            self.assertFalse(is_valid)


class TestEpubGeneratorPerformance(unittest.TestCase):
    """Test performance aspects of EpubGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = EpubGenerator()
        
        # Create a test cover image
        self.cover_path = os.path.join(self.temp_dir, 'test_cover.png')
        test_cover_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(self.cover_path, 'wb') as f:
            f.write(test_cover_data)
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_large_book_generation(self):
        """Test generation of large book."""
        import time
        
        # Create large book data
        large_data = [
            {'type': 'title', 'content': 'Large Test Book'},
            {'type': 'author', 'content': 'Performance Test Author'},
            {'type': 'cover', 'image': self.cover_path},
        ]
        
        # Add 20 chapters with substantial content
        for chapter in range(1, 21):
            large_data.append({'type': 'chapter_header', 'content': str(chapter)})
            
            # Add multiple paragraphs per chapter
            for para in range(10):
                content = f"This is paragraph {para + 1} of chapter {chapter}. " * 20
                large_data.append({'type': 'paragraph', 'content': content})
                
        epub_path = os.path.join(self.temp_dir, 'large_book.epub')
        
        start_time = time.time()
        self.generator.generate_epub(large_data, epub_path, self.temp_dir)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 30 seconds)
        generation_time = end_time - start_time
        self.assertLess(generation_time, 30.0)
        
        # Should create valid EPUB
        self.assertTrue(os.path.exists(epub_path))
        
        # Check file size is reasonable
        file_size = os.path.getsize(epub_path)
        self.assertGreater(file_size, 10000)  # Should be substantial
        
    def test_memory_usage(self):
        """Test memory usage during generation."""
        # This is a basic test - in a real scenario you might use memory profiling
        test_data = [
            {'type': 'title', 'content': 'Memory Test Book'},
            {'type': 'author', 'content': 'Test Author'},
            {'type': 'cover', 'image': self.cover_path},
        ]
        
        # Add moderate amount of content
        for i in range(100):
            test_data.append({
                'type': 'paragraph', 
                'content': f'Test paragraph {i} with some content. ' * 10
            })
            
        epub_path = os.path.join(self.temp_dir, 'memory_test.epub')
        
        # Should complete without memory errors
        self.generator.generate_epub(test_data, epub_path, self.temp_dir)
        
        self.assertTrue(os.path.exists(epub_path))


if __name__ == '__main__':
    unittest.main()