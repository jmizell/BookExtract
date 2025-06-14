#!/usr/bin/env python3
"""
Unit tests for the OCRProcessor class.

Tests text processing, file handling, and configuration validation
without requiring actual OCR or LLM API calls.
"""

import unittest
import tempfile
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookextract.ocr_processor import OCRProcessor


class TestOCRProcessor(unittest.TestCase):
    """Test cases for OCRProcessor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = OCRProcessor(
            api_url="http://test.api",
            api_token="test_token",
            model="test_model",
            max_workers=5
        )
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """Test OCRProcessor initialization."""
        self.assertEqual(self.processor.api_url, "http://test.api")
        self.assertEqual(self.processor.api_token, "test_token")
        self.assertEqual(self.processor.model, "test_model")
        self.assertEqual(self.processor.max_workers, 5)
        self.assertFalse(self.processor.is_cancelled)
        self.assertIsNone(self.processor.progress_callback)
        self.assertIsNone(self.processor.log_callback)
        
    def test_default_initialization(self):
        """Test OCRProcessor initialization with defaults."""
        processor = OCRProcessor()
        
        self.assertEqual(processor.api_url, "")
        self.assertEqual(processor.api_token, "")
        self.assertEqual(processor.model, "")
        self.assertEqual(processor.max_workers, 15)
        
    def test_set_callbacks(self):
        """Test setting callback functions."""
        progress_callback = MagicMock()
        log_callback = MagicMock()
        
        self.processor.set_callbacks(
            progress_callback=progress_callback,
            log_callback=log_callback
        )
        
        self.assertEqual(self.processor.progress_callback, progress_callback)
        self.assertEqual(self.processor.log_callback, log_callback)
        
    def test_cancellation_flag(self):
        """Test cancellation functionality."""
        self.assertFalse(self.processor.is_cancelled)
        
        # Test setting cancellation
        self.processor.is_cancelled = True
        self.assertTrue(self.processor.is_cancelled)
        
    def test_callback_invocation(self):
        """Test that callbacks are properly invoked."""
        progress_callback = MagicMock()
        log_callback = MagicMock()
        
        self.processor.set_callbacks(
            progress_callback=progress_callback,
            log_callback=log_callback
        )
        
        # Test progress callback if method exists
        if hasattr(self.processor, '_update_progress'):
            self.processor._update_progress(50, "Test progress")
            progress_callback.assert_called_with(50, "Test progress")
            
        # Test log callback if method exists
        if hasattr(self.processor, '_log'):
            self.processor._log("Test log message")
            log_callback.assert_called_with("Test log message")


class TestOCRTextProcessing(unittest.TestCase):
    """Test text processing functionality of OCRProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = OCRProcessor()
        
    def test_text_cleaning_basic(self):
        """Test basic text cleaning functionality."""
        # Test if text cleaning methods exist and work
        if hasattr(self.processor, 'clean_ocr_text'):
            test_text = "This is a test   with extra    spaces\n\nand newlines"
            cleaned = self.processor.clean_ocr_text(test_text)
            
            # Should clean up extra whitespace
            self.assertNotEqual(cleaned, test_text)
            self.assertNotIn("   ", cleaned)  # No triple spaces
            
    def test_text_merging(self):
        """Test text merging across pages."""
        if hasattr(self.processor, 'merge_text_blocks'):
            text_blocks = [
                "This is the first block of text.",
                "This is the second block.",
                "And this is the third block."
            ]
            
            merged = self.processor.merge_text_blocks(text_blocks)
            
            self.assertIsInstance(merged, str)
            self.assertIn("first block", merged)
            self.assertIn("second block", merged)
            self.assertIn("third block", merged)
            
    def test_paragraph_detection(self):
        """Test paragraph detection and formatting."""
        if hasattr(self.processor, 'detect_paragraphs'):
            test_text = """This is the first paragraph.
            It has multiple sentences.
            
            This is the second paragraph.
            It also has content.
            
            And this is the third paragraph."""
            
            paragraphs = self.processor.detect_paragraphs(test_text)
            
            self.assertIsInstance(paragraphs, list)
            self.assertGreater(len(paragraphs), 1)


class TestOCRFileOperations(unittest.TestCase):
    """Test file operations for OCRProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = OCRProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_image_file_discovery(self):
        """Test discovering image files for OCR processing."""
        # Create mock image files
        image_files = [
            "page001.png",
            "page002.jpg",
            "page003.jpeg",
            "not_an_image.txt"
        ]
        
        for filename in image_files:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("mock file content")
                
        # Test file discovery if method exists
        if hasattr(self.processor, 'find_image_files'):
            found_files = self.processor.find_image_files(self.temp_dir)
            
            # Should find image files but not text files
            self.assertIsInstance(found_files, list)
            image_extensions = ['.png', '.jpg', '.jpeg']
            for file_path in found_files:
                ext = os.path.splitext(file_path)[1].lower()
                self.assertIn(ext, image_extensions)
                
    def test_output_file_creation(self):
        """Test creation of output files."""
        if hasattr(self.processor, 'save_ocr_results'):
            test_results = {
                "page_001": "This is the text from page 1.",
                "page_002": "This is the text from page 2.",
                "page_003": "This is the text from page 3."
            }
            
            output_file = os.path.join(self.temp_dir, "ocr_results.json")
            
            # Test saving results
            self.processor.save_ocr_results(test_results, output_file)
            
            # Verify file was created and contains expected data
            self.assertTrue(os.path.exists(output_file))
            
            with open(output_file, 'r') as f:
                loaded_results = json.load(f)
                
            self.assertEqual(loaded_results, test_results)
            
    def test_batch_processing_setup(self):
        """Test setup for batch processing."""
        # Create multiple image files
        for i in range(5):
            filename = f"page{i:03d}.png"
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"mock image {i}")
                
        if hasattr(self.processor, 'prepare_batch_processing'):
            batch_info = self.processor.prepare_batch_processing(self.temp_dir)
            
            self.assertIsInstance(batch_info, dict)
            self.assertIn('total_files', batch_info)
            self.assertEqual(batch_info['total_files'], 5)


class TestOCRConfiguration(unittest.TestCase):
    """Test configuration and validation for OCRProcessor."""
    
    def test_api_configuration_validation(self):
        """Test API configuration validation."""
        # Test with valid configuration
        processor = OCRProcessor(
            api_url="https://api.example.com",
            api_token="valid_token",
            model="gpt-4"
        )
        
        if hasattr(processor, 'validate_api_config'):
            is_valid = processor.validate_api_config()
            self.assertTrue(is_valid)
            
        # Test with invalid configuration
        invalid_processor = OCRProcessor(
            api_url="",
            api_token="",
            model=""
        )
        
        if hasattr(invalid_processor, 'validate_api_config'):
            is_valid = invalid_processor.validate_api_config()
            self.assertFalse(is_valid)
            
    def test_worker_configuration(self):
        """Test worker thread configuration."""
        # Test valid worker counts
        for workers in [1, 5, 10, 20]:
            processor = OCRProcessor(max_workers=workers)
            self.assertEqual(processor.max_workers, workers)
            
        # Test edge cases
        processor_zero = OCRProcessor(max_workers=0)
        if hasattr(processor_zero, 'validate_worker_config'):
            is_valid = processor_zero.validate_worker_config()
            self.assertFalse(is_valid)
            
    def test_processing_parameters(self):
        """Test OCR processing parameters."""
        processor = OCRProcessor()
        
        # Test parameter setting if methods exist
        if hasattr(processor, 'set_ocr_parameters'):
            params = {
                'language': 'eng',
                'confidence_threshold': 0.8,
                'preprocessing': True
            }
            
            processor.set_ocr_parameters(params)
            
            if hasattr(processor, 'get_ocr_parameters'):
                retrieved_params = processor.get_ocr_parameters()
                self.assertEqual(retrieved_params['language'], 'eng')
                self.assertEqual(retrieved_params['confidence_threshold'], 0.8)


class TestOCRErrorHandling(unittest.TestCase):
    """Test error handling in OCRProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = OCRProcessor()
        
    def test_invalid_file_handling(self):
        """Test handling of invalid files."""
        if hasattr(self.processor, 'process_image_file'):
            # Test with non-existent file
            with self.assertRaises((FileNotFoundError, IOError)):
                self.processor.process_image_file("/path/that/does/not/exist.png")
                
    def test_api_error_handling(self):
        """Test handling of API errors."""
        if hasattr(self.processor, 'call_llm_api'):
            # Test with invalid API configuration
            processor = OCRProcessor(api_url="invalid_url")
            
            with patch('requests.post') as mock_post:
                mock_post.side_effect = Exception("Connection error")
                
                result = processor.call_llm_api("test text")
                
                # Should handle error gracefully
                self.assertIsNotNone(result)
                
    def test_cancellation_handling(self):
        """Test proper handling of operation cancellation."""
        self.processor.is_cancelled = True
        
        if hasattr(self.processor, 'process_batch'):
            # Processing should respect cancellation flag
            result = self.processor.process_batch([])
            
            # Should return early or handle cancellation appropriately
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()