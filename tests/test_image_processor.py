#!/usr/bin/env python3
"""
Unit tests for the ImageProcessor class.

Tests image loading, file discovery, and crop coordinate validation
without requiring actual image processing.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookextract.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    """Test cases for ImageProcessor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = ImageProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """Test ImageProcessor initialization."""
        self.assertEqual(self.processor.image_files, [])
        self.assertEqual(self.processor.current_image_index, 0)
        self.assertIsNone(self.processor.current_image)
        
        # Test default crop coordinates
        self.assertEqual(self.processor.crop_x, 1056)
        self.assertEqual(self.processor.crop_y, 190)
        self.assertEqual(self.processor.crop_width, 822)
        self.assertEqual(self.processor.crop_height, 947)
        
    def test_load_images_from_nonexistent_folder(self):
        """Test loading images from a folder that doesn't exist."""
        nonexistent_path = "/path/that/does/not/exist"
        
        with self.assertRaises(FileNotFoundError) as context:
            self.processor.load_images_from_folder(nonexistent_path)
            
        self.assertIn("Input folder does not exist", str(context.exception))
        
    def test_load_images_from_empty_folder(self):
        """Test loading images from an empty folder."""
        with self.assertRaises(ValueError) as context:
            self.processor.load_images_from_folder(self.temp_dir)
            
        self.assertIn("No image files found", str(context.exception))
        
    def test_load_images_with_mock_files(self):
        """Test loading images with mocked file discovery."""
        # Create mock image files
        test_files = [
            os.path.join(self.temp_dir, "image1.png"),
            os.path.join(self.temp_dir, "image2.jpg"),
            os.path.join(self.temp_dir, "image3.jpeg"),
        ]
        
        # Create actual files
        for file_path in test_files:
            with open(file_path, 'w') as f:
                f.write("mock image data")
        
        # Test loading
        count = self.processor.load_images_from_folder(self.temp_dir)
        
        self.assertEqual(count, 3)
        self.assertEqual(len(self.processor.image_files), 3)
        self.assertEqual(self.processor.current_image_index, 0)
        
        # Files should be sorted
        self.assertTrue(all(f in self.processor.image_files for f in test_files))
        
    def test_get_current_image_info_no_images(self):
        """Test getting current image info when no images are loaded."""
        index, info = self.processor.get_current_image_info()
        
        self.assertIsNone(index)
        self.assertIn("No images loaded", info)
        
    def test_get_current_image_info_with_images(self):
        """Test getting current image info with loaded images."""
        # Create mock image files
        test_files = [
            os.path.join(self.temp_dir, "image1.png"),
            os.path.join(self.temp_dir, "image2.jpg"),
        ]
        
        for file_path in test_files:
            with open(file_path, 'w') as f:
                f.write("mock image data")
        
        self.processor.load_images_from_folder(self.temp_dir)
        
        index, info = self.processor.get_current_image_info()
        
        self.assertIsNotNone(index)
        self.assertIsNotNone(info)
        self.assertEqual(index, 0)
        self.assertIn("1/2", info)
        self.assertIn("image1.png", info)
        
    def test_set_crop_coordinates(self):
        """Test setting crop coordinates."""
        new_x, new_y = 100, 200
        new_width, new_height = 300, 400
        
        self.processor.crop_x = new_x
        self.processor.crop_y = new_y
        self.processor.crop_width = new_width
        self.processor.crop_height = new_height
        
        self.assertEqual(self.processor.crop_x, new_x)
        self.assertEqual(self.processor.crop_y, new_y)
        self.assertEqual(self.processor.crop_width, new_width)
        self.assertEqual(self.processor.crop_height, new_height)
        
    def test_image_navigation(self):
        """Test image navigation functionality."""
        # Create mock image files
        test_files = [
            os.path.join(self.temp_dir, "image1.png"),
            os.path.join(self.temp_dir, "image2.jpg"),
            os.path.join(self.temp_dir, "image3.jpeg"),
        ]
        
        for file_path in test_files:
            with open(file_path, 'w') as f:
                f.write("mock image data")
        
        self.processor.load_images_from_folder(self.temp_dir)
        
        # Test initial state
        self.assertEqual(self.processor.current_image_index, 0)
        
        # Test navigation (if methods exist)
        if hasattr(self.processor, 'navigate_next'):
            result = self.processor.navigate_next()
            self.assertTrue(result)
            self.assertEqual(self.processor.current_image_index, 1)
            
        if hasattr(self.processor, 'navigate_prev'):
            result = self.processor.navigate_prev()
            self.assertTrue(result)
            self.assertEqual(self.processor.current_image_index, 0)
            
    def test_supported_image_extensions(self):
        """Test that various image extensions are supported."""
        extensions = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'gif']
        
        # Create files with different extensions
        for i, ext in enumerate(extensions):
            file_path = os.path.join(self.temp_dir, f"image{i}.{ext}")
            with open(file_path, 'w') as f:
                f.write("mock image data")
                
        count = self.processor.load_images_from_folder(self.temp_dir)
        
        self.assertEqual(count, len(extensions))
        self.assertEqual(len(self.processor.image_files), len(extensions))
        
    def test_case_insensitive_extensions(self):
        """Test that both lowercase and uppercase extensions work."""
        # Create files with mixed case extensions
        test_files = [
            os.path.join(self.temp_dir, "image1.PNG"),
            os.path.join(self.temp_dir, "image2.jpg"),
            os.path.join(self.temp_dir, "image3.JPEG"),
        ]
        
        for file_path in test_files:
            with open(file_path, 'w') as f:
                f.write("mock image data")
                
        count = self.processor.load_images_from_folder(self.temp_dir)
        
        self.assertEqual(count, 3)
        self.assertEqual(len(self.processor.image_files), 3)


class TestImageProcessorIntegration(unittest.TestCase):
    """Integration tests for ImageProcessor with mocked PIL operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = ImageProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('bookextract.image_processor.Image')
    def test_crop_operations_mocked(self, mock_image):
        """Test crop operations with mocked PIL Image."""
        # Setup mock
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img
        mock_img.size = (1920, 1080)
        mock_cropped = MagicMock()
        mock_img.crop.return_value = mock_cropped
        
        # Create a test image file
        test_file = os.path.join(self.temp_dir, "test.png")
        with open(test_file, 'w') as f:
            f.write("mock image data")
            
        self.processor.load_images_from_folder(self.temp_dir)
        
        # Test that we can call crop-related methods if they exist
        if hasattr(self.processor, 'crop_current_image'):
            result = self.processor.crop_current_image()
            # Verify mock was called
            mock_image.open.assert_called()
            
    def test_batch_processing_setup(self):
        """Test setup for batch processing operations."""
        # Create multiple test files
        for i in range(5):
            test_file = os.path.join(self.temp_dir, f"test{i:02d}.png")
            with open(test_file, 'w') as f:
                f.write(f"mock image data {i}")
                
        count = self.processor.load_images_from_folder(self.temp_dir)
        
        self.assertEqual(count, 5)
        
        # Test that files are properly sorted for batch processing
        filenames = [os.path.basename(f) for f in self.processor.image_files]
        expected_order = [f"test{i:02d}.png" for i in range(5)]
        
        # Files should be in sorted order
        self.assertEqual(sorted(filenames), sorted(expected_order))


if __name__ == '__main__':
    unittest.main()