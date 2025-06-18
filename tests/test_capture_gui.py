#!/usr/bin/env python3
"""
Tests for the Capture GUI tool.

This module tests the unified book capture and crop functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from pathlib import Path
import sys

# Add the parent directory to the path to import the capture_gui module
sys.path.insert(0, str(Path(__file__).parent.parent))

from capture_gui import UnifiedBookTool


class TestUnifiedBookTool(unittest.TestCase):
    """Test cases for the UnifiedBookTool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock root window to avoid GUI display during tests
        self.root = Mock(spec=tk.Tk)
        self.root.title = Mock()
        self.root.geometry = Mock()
        self.root.resizable = Mock()
        self.root.bind = Mock()
        self.root.protocol = Mock()
        self.root.config = Mock()
        self.root.columnconfigure = Mock()
        self.root.rowconfigure = Mock()
        self.root.after = Mock()
        self.root.update_idletasks = Mock()
        
        # Mock the GUI components
        with patch('capture_gui.ttk'), \
             patch('capture_gui.tk'), \
             patch('capture_gui.messagebox'), \
             patch('capture_gui.filedialog'):
            self.tool = UnifiedBookTool(self.root)
            
    def test_initialization(self):
        """Test that the tool initializes correctly."""
        self.assertIsNotNone(self.tool.capture_handler)
        self.assertEqual(self.tool.default_output_folder, str(Path.cwd() / "out"))
        self.assertIsNone(self.tool.preview_image)
        self.assertIsNone(self.tool.current_preview_path)
        
    def test_get_capture_params(self):
        """Test getting capture parameters from GUI inputs."""
        # Mock the StringVar objects
        self.tool.pages_var = Mock()
        self.tool.pages_var.get.return_value = "100"
        self.tool.delay_var = Mock()
        self.tool.delay_var.get.return_value = "1.0"
        self.tool.output_folder_var = Mock()
        self.tool.output_folder_var.get.return_value = "/test/output"
        self.tool.next_x_var = Mock()
        self.tool.next_x_var.get.return_value = "1000"
        self.tool.next_y_var = Mock()
        self.tool.next_y_var.get.return_value = "500"
        self.tool.safe_x_var = Mock()
        self.tool.safe_x_var.get.return_value = "50"
        self.tool.safe_y_var = Mock()
        self.tool.safe_y_var.get.return_value = "500"
        self.tool.initial_seq_var = Mock()
        self.tool.initial_seq_var.get.return_value = "1"
        self.tool.crop_x_var = Mock()
        self.tool.crop_x_var.get.return_value = "100"
        self.tool.crop_y_var = Mock()
        self.tool.crop_y_var.get.return_value = "200"
        self.tool.crop_width_var = Mock()
        self.tool.crop_width_var.get.return_value = "800"
        self.tool.crop_height_var = Mock()
        self.tool.crop_height_var.get.return_value = "600"
        
        params = self.tool.get_capture_params()
        
        expected_params = {
            'pages': "100",
            'delay': "1.0",
            'save_location': "/test/output",
            'next_x': "1000",
            'next_y': "500",
            'safe_x': "50",
            'safe_y': "500",
            'initial_seq': "1",
            'crop_x': "100",
            'crop_y': "200",
            'crop_width': "800",
            'crop_height': "600"
        }
        
        self.assertEqual(params, expected_params)
        
    def test_validate_inputs_valid(self):
        """Test input validation with valid inputs."""
        # Mock the get_capture_params method
        self.tool.get_capture_params = Mock(return_value={
            'pages': "10",
            'delay': "0.5",
            'save_location': "/test/output",
            'next_x': "1000",
            'next_y': "500",
            'safe_x': "50",
            'safe_y': "500",
            'crop_x': "100",
            'crop_y': "200",
            'crop_width': "800",
            'crop_height': "600"
        })
        
        # Mock the capture handler validation
        self.tool.capture_handler.validate_capture_params = Mock(return_value=(True, ""))
        
        with patch('capture_gui.messagebox'):
            result = self.tool.validate_inputs()
            
        self.assertTrue(result)
        
    def test_validate_inputs_invalid_capture_params(self):
        """Test input validation with invalid capture parameters."""
        # Mock the get_capture_params method
        self.tool.get_capture_params = Mock(return_value={
            'pages': "-1",  # Invalid
            'delay': "0.5",
            'save_location': "/test/output",
            'next_x': "1000",
            'next_y': "500",
            'safe_x': "50",
            'safe_y': "500",
            'crop_x': "100",
            'crop_y': "200",
            'crop_width': "800",
            'crop_height': "600"
        })
        
        # Mock the capture handler validation
        self.tool.capture_handler.validate_capture_params = Mock(return_value=(False, "Invalid pages"))
        
        with patch('capture_gui.messagebox') as mock_messagebox:
            result = self.tool.validate_inputs()
            
        self.assertFalse(result)
        mock_messagebox.showerror.assert_called_once()
        
    def test_validate_inputs_invalid_crop_params(self):
        """Test input validation with invalid crop parameters."""
        # Mock the get_capture_params method
        self.tool.get_capture_params = Mock(return_value={
            'pages': "10",
            'delay': "0.5",
            'save_location': "/test/output",
            'next_x': "1000",
            'next_y': "500",
            'safe_x': "50",
            'safe_y': "500",
            'crop_x': "-100",  # Invalid
            'crop_y': "200",
            'crop_width': "800",
            'crop_height': "600"
        })
        
        # Mock the capture handler validation
        self.tool.capture_handler.validate_capture_params = Mock(return_value=(True, ""))
        
        with patch('capture_gui.messagebox') as mock_messagebox:
            result = self.tool.validate_inputs()
            
        self.assertFalse(result)
        mock_messagebox.showerror.assert_called_once()
        
    def test_reset_defaults(self):
        """Test resetting to default values."""
        # Mock the StringVar objects
        self.tool.pages_var = Mock()
        self.tool.initial_seq_var = Mock()
        self.tool.delay_var = Mock()
        self.tool.output_folder_var = Mock()
        self.tool.next_x_var = Mock()
        self.tool.next_y_var = Mock()
        self.tool.safe_x_var = Mock()
        self.tool.safe_y_var = Mock()
        self.tool.crop_x_var = Mock()
        self.tool.crop_y_var = Mock()
        self.tool.crop_width_var = Mock()
        self.tool.crop_height_var = Mock()
        self.tool.log_message = Mock()
        
        self.tool.reset_defaults()
        
        # Verify all variables are set to default values
        self.tool.pages_var.set.assert_called_with("380")
        self.tool.initial_seq_var.set.assert_called_with("0")
        self.tool.delay_var.set.assert_called_with("0.5")
        self.tool.output_folder_var.set.assert_called_with(self.tool.default_output_folder)
        self.tool.next_x_var.set.assert_called_with("1865")
        self.tool.next_y_var.set.assert_called_with("650")
        self.tool.safe_x_var.set.assert_called_with("30")
        self.tool.safe_y_var.set.assert_called_with("650")
        self.tool.crop_x_var.set.assert_called_with("1056")
        self.tool.crop_y_var.set.assert_called_with("190")
        self.tool.crop_width_var.set.assert_called_with("822")
        self.tool.crop_height_var.set.assert_called_with("947")
        self.tool.log_message.assert_called_with("Settings reset to defaults")
        
    def test_log_message(self):
        """Test logging functionality."""
        # Mock the status text widget
        self.tool.status_text = Mock()
        
        message = "Test log message"
        self.tool.log_message(message)
        
        # Verify the message was inserted
        self.tool.status_text.insert.assert_called_once()
        self.tool.status_text.see.assert_called_once_with(tk.END)
        
    def test_update_progress(self):
        """Test progress update functionality."""
        # Mock the progress components
        self.tool.progress_bar = Mock()
        self.tool.progress_var = Mock()
        
        current = 5
        status = "Processing page 5/10"
        
        self.tool.update_progress(current, status)
        
        self.tool.progress_bar.config.assert_called_with(value=current)
        self.tool.progress_var.set.assert_called_with(status)
        
    def test_on_capture_complete_success(self):
        """Test capture completion handling for successful completion."""
        # Mock the UI components
        self.tool.start_button = Mock()
        self.tool.cancel_button = Mock()
        self.tool.progress_var = Mock()
        self.tool.progress_bar = Mock()
        self.tool.pages_var = Mock()
        self.tool.pages_var.get.return_value = "10"
        
        self.tool.on_capture_complete(True, "Completed successfully")
        
        self.tool.start_button.config.assert_called_with(state=tk.NORMAL)
        self.tool.cancel_button.config.assert_called_with(state=tk.DISABLED)
        self.tool.progress_var.set.assert_called_with("Completed successfully")
        self.tool.progress_bar.config.assert_called_with(value=10)
        
    def test_on_capture_complete_failure(self):
        """Test capture completion handling for failed completion."""
        # Mock the UI components
        self.tool.start_button = Mock()
        self.tool.cancel_button = Mock()
        self.tool.progress_var = Mock()
        self.tool.progress_bar = Mock()
        
        self.tool.on_capture_complete(False, "Capture failed")
        
        self.tool.start_button.config.assert_called_with(state=tk.NORMAL)
        self.tool.cancel_button.config.assert_called_with(state=tk.DISABLED)
        self.tool.progress_var.set.assert_called_with("Capture failed")
        # Progress bar should not be updated on failure
        self.tool.progress_bar.config.assert_not_called()
        
    @patch('capture_gui.subprocess.run')
    def test_take_test_screenshot_success(self, mock_subprocess):
        """Test taking a test screenshot successfully."""
        # Mock subprocess success
        mock_subprocess.return_value = Mock()

        # Create a simple string path that we can track
        test_path = "/mock_dir/preview.png"

        # Mock the output folder and path operations
        self.tool.output_folder_var = Mock()
        self.tool.output_folder_var.get.return_value = "/mock_dir"

        with patch('capture_gui.Path') as mock_path_class:
            # Configure the Path mock to return consistent values
            mock_path_instance = Mock()
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.mkdir = Mock()

            # Create a mock for the preview.png path that will be used
            mock_preview_path = Mock()
            mock_path_instance.__truediv__ = Mock(return_value=mock_preview_path)
            mock_preview_path.__str__ = Mock(return_value=test_path)

            # Mock the log_message and load_preview_image methods
            self.tool.log_message = Mock()
            self.tool.load_preview_image = Mock()

            self.tool.take_test_screenshot()

            # Verify subprocess was called with the string representation
            mock_subprocess.assert_called_once_with(
                ['import', '-window', 'root', test_path],
                check=True, capture_output=True
            )

            # Verify the preview was loaded
            self.assertEqual(self.tool.current_preview_path, mock_preview_path)
            self.tool.load_preview_image.assert_called_once()
            self.tool.log_message.assert_called_with("Test screenshot taken and loaded for preview")
            
    @patch('capture_gui.subprocess.run')
    def test_take_test_screenshot_failure(self, mock_subprocess):
        """Test taking a test screenshot with failure."""
        # Mock subprocess failure
        from subprocess import CalledProcessError
        mock_subprocess.side_effect = CalledProcessError(1, 'import')
        
        # Mock messagebox and log_message
        with patch('capture_gui.messagebox') as mock_messagebox:
            self.tool.log_message = Mock()
            
            self.tool.take_test_screenshot()
            
            # Verify error handling
            mock_messagebox.showerror.assert_called_once()
            self.tool.log_message.assert_called()
            
    def test_cancel_capture(self):
        """Test canceling the capture process."""
        self.tool.capture_handler.cancel_capture = Mock()
        
        self.tool.cancel_capture()
        
        self.tool.capture_handler.cancel_capture.assert_called_once()


if __name__ == '__main__':
    unittest.main()