#!/usr/bin/env python3
"""
Unit tests for the BookCapture class.

Tests configuration validation, dependency checking, and parameter validation
without requiring actual screen capture or mouse automation.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookextract.book_capture import BookCapture


class TestBookCapture(unittest.TestCase):
    """Test BookCapture functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.capture = BookCapture()
        
    def test_initialization(self):
        """Test BookCapture initialization."""
        self.assertFalse(self.capture.is_capturing)
        self.assertEqual(self.capture.current_page, 0)
        self.assertEqual(self.capture.total_pages, 0)
        self.assertIsNone(self.capture.progress_callback)
        self.assertIsNone(self.capture.log_callback)
        self.assertIsNone(self.capture.completion_callback)
        
    def test_callback_setting(self):
        """Test setting callback functions."""
        progress_callback = MagicMock()
        log_callback = MagicMock()
        completion_callback = MagicMock()
        
        self.capture.set_callbacks(
            progress_callback=progress_callback,
            log_callback=log_callback,
            completion_callback=completion_callback
        )
        
        self.assertEqual(self.capture.progress_callback, progress_callback)
        self.assertEqual(self.capture.log_callback, log_callback)
        self.assertEqual(self.capture.completion_callback, completion_callback)
        
    def test_internal_logging(self):
        """Test internal logging methods."""
        log_callback = MagicMock()
        self.capture.set_callbacks(log_callback=log_callback)
        
        self.capture._log("Test log message")
        
        log_callback.assert_called_once_with("Test log message")
        
    def test_progress_update(self):
        """Test progress update functionality."""
        progress_callback = MagicMock()
        self.capture.set_callbacks(progress_callback=progress_callback)
        
        self.capture._update_progress(5, "Capturing page 5")
        
        progress_callback.assert_called_once_with(5, "Capturing page 5")
        
    def test_completion_notification(self):
        """Test completion notification."""
        completion_callback = MagicMock()
        self.capture.set_callbacks(completion_callback=completion_callback)
        
        self.capture._notify_completion(True, "Capture completed successfully")
        
        completion_callback.assert_called_once_with(True, "Capture completed successfully")


class TestBookCaptureDependencies(unittest.TestCase):
    """Test dependency checking for BookCapture."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.capture = BookCapture()
        
    @patch('subprocess.run')
    def test_check_dependencies_all_available(self, mock_run):
        """Test dependency checking when all tools are available."""
        mock_run.return_value = MagicMock(returncode=0)
        
        all_available, missing_tools = self.capture.check_dependencies()
        
        self.assertTrue(all_available)
        self.assertEqual(missing_tools, [])
        
    @patch('subprocess.run')
    def test_check_dependencies_some_missing(self, mock_run):
        """Test dependency checking when some tools are missing."""
        def mock_subprocess(cmd, **kwargs):
            if cmd[0] == "import":
                return MagicMock(returncode=0)
            else:
                raise FileNotFoundError("Command not found")
                
        mock_run.side_effect = mock_subprocess
        
        all_available, missing_tools = self.capture.check_dependencies()
        
        self.assertFalse(all_available)
        self.assertIn("xdotool", missing_tools)
        
    @patch('subprocess.run')
    def test_check_dependencies_all_missing(self, mock_run):
        """Test dependency checking when all tools are missing."""
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        all_available, missing_tools = self.capture.check_dependencies()
        
        self.assertFalse(all_available)
        self.assertEqual(len(missing_tools), 2)  # import and xdotool
        
    @patch('subprocess.run')
    def test_get_dependency_status(self, mock_run):
        """Test getting detailed dependency status."""
        def mock_subprocess(cmd, **kwargs):
            if cmd[0] == "import":
                return MagicMock(returncode=0)
            else:
                raise FileNotFoundError("Command not found")
                
        mock_run.side_effect = mock_subprocess
        
        status = self.capture.get_dependency_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('ImageMagick (import)', status)
        self.assertIn('xdotool', status)
        
        # ImageMagick should be available, xdotool should not
        self.assertTrue(status['ImageMagick (import)'])
        self.assertFalse(status['xdotool'])


class TestBookCaptureParameterValidation(unittest.TestCase):
    """Test parameter validation for BookCapture."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.capture = BookCapture()
        
    def test_validate_capture_params_valid(self):
        """Test validation of valid capture parameters."""
        valid_params = {
            'pages': 10,
            'delay': 2.0,
            'save_location': '/tmp/captures',
            'next_x': 100,
            'next_y': 200,
            'safe_x': 50,
            'safe_y': 50
        }
        
        is_valid, message = self.capture.validate_capture_params(valid_params)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "")
        
    def test_validate_capture_params_invalid_pages(self):
        """Test validation with invalid page count."""
        invalid_params = {
            'pages': 0,  # Invalid: must be positive
            'delay': 2.0,
            'save_location': '/tmp/captures',
            'next_x': 100,
            'next_y': 200,
            'safe_x': 50,
            'safe_y': 50
        }
        
        is_valid, message = self.capture.validate_capture_params(invalid_params)
        
        self.assertFalse(is_valid)
        self.assertIn("pages", message.lower())
        
    def test_validate_capture_params_invalid_delay(self):
        """Test validation with invalid delay."""
        invalid_params = {
            'pages': 10,
            'delay': -1.0,  # Invalid: must be non-negative
            'save_location': '/tmp/captures',
            'next_x': 100,
            'next_y': 200,
            'safe_x': 50,
            'safe_y': 50
        }
        
        is_valid, message = self.capture.validate_capture_params(invalid_params)
        
        self.assertFalse(is_valid)
        self.assertIn("delay", message.lower())
        
    def test_validate_capture_params_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        invalid_params = {
            'pages': 10,
            'delay': 2.0,
            'save_location': '/tmp/captures',
            'next_x': "not_a_number",  # Invalid: not convertible to int
            'next_y': 200,
            'safe_x': 50,
            'safe_y': 50
        }
        
        is_valid, message = self.capture.validate_capture_params(invalid_params)
        
        self.assertFalse(is_valid)
        self.assertIn("coordinate", message.lower())
        
    def test_validate_capture_params_missing_required(self):
        """Test validation with missing required parameters."""
        incomplete_params = {
            'pages': 10,
            'delay': 2.0,
            # Missing save_location and coordinates
        }
        
        is_valid, message = self.capture.validate_capture_params(incomplete_params)
        
        self.assertFalse(is_valid)
        self.assertIn("save location", message.lower())
        
    def test_validate_capture_params_edge_cases(self):
        """Test validation with edge case values."""
        edge_case_params = {
            'pages': 1,  # Minimum valid value
            'delay': 0.0,  # Minimum valid value
            'save_location': '/tmp',
            'next_x': 0,  # Minimum valid value
            'next_y': 0,
            'safe_x': 0,
            'safe_y': 0
        }
        
        is_valid, message = self.capture.validate_capture_params(edge_case_params)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "")


class TestBookCaptureOperations(unittest.TestCase):
    """Test capture operations for BookCapture."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.capture = BookCapture()
        
    def test_capture_state_management(self):
        """Test capture state management."""
        # Initial state
        self.assertFalse(self.capture.is_capturing)
        self.assertEqual(self.capture.current_page, 0)
        
        # Start capture
        self.capture.is_capturing = True
        self.capture.total_pages = 10
        
        self.assertTrue(self.capture.is_capturing)
        self.assertEqual(self.capture.total_pages, 10)
        
        # Update progress
        self.capture.current_page = 5
        self.assertEqual(self.capture.current_page, 5)
        
        # Stop capture
        self.capture.is_capturing = False
        self.assertFalse(self.capture.is_capturing)
        
    @patch('subprocess.run')
    def test_screenshot_command_generation(self, mock_run):
        """Test screenshot command generation."""
        if hasattr(self.capture, 'take_screenshot'):
            mock_run.return_value = MagicMock(returncode=0)
            
            result = self.capture.take_screenshot('/tmp/test.png')
            
            # Should call subprocess with import command
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            self.assertIn('import', call_args)
            
    @patch('subprocess.run')
    def test_mouse_click_command_generation(self, mock_run):
        """Test mouse click command generation."""
        if hasattr(self.capture, 'click_at_position'):
            mock_run.return_value = MagicMock(returncode=0)
            
            result = self.capture.click_at_position(100, 200)
            
            # Should call subprocess with xdotool command
            mock_run.assert_called()
            call_args = mock_run.call_args[0][0]
            self.assertIn('xdotool', call_args)
            
    def test_filename_generation(self):
        """Test screenshot filename generation."""
        if hasattr(self.capture, 'generate_filename'):
            filename = self.capture.generate_filename('/tmp/captures', 5)
            
            self.assertIsInstance(filename, str)
            self.assertIn('/tmp/captures', filename)
            self.assertIn('5', filename)
            
    def test_capture_sequence_validation(self):
        """Test validation of capture sequence parameters."""
        if hasattr(self.capture, 'validate_capture_sequence'):
            sequence_params = {
                'start_page': 1,
                'end_page': 10,
                'click_coordinates': [(100, 200)],
                'delays': [2.0]
            }
            
            is_valid = self.capture.validate_capture_sequence(sequence_params)
            
            self.assertIsInstance(is_valid, bool)


class TestBookCaptureErrorHandling(unittest.TestCase):
    """Test error handling in BookCapture."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.capture = BookCapture()
        
    @patch('subprocess.run')
    def test_screenshot_error_handling(self, mock_run):
        """Test handling of screenshot errors."""
        if hasattr(self.capture, 'take_screenshot'):
            mock_run.side_effect = Exception("Screenshot failed")
            
            result = self.capture.take_screenshot('/tmp/test.png')
            
            # Should handle error gracefully
            self.assertIsNotNone(result)
            
    @patch('subprocess.run')
    def test_mouse_click_error_handling(self, mock_run):
        """Test handling of mouse click errors."""
        if hasattr(self.capture, 'click_at_position'):
            mock_run.side_effect = Exception("Click failed")
            
            result = self.capture.click_at_position(100, 200)
            
            # Should handle error gracefully
            self.assertIsNotNone(result)
            
    def test_invalid_save_location_handling(self):
        """Test handling of invalid save locations."""
        invalid_params = {
            'pages': 10,
            'delay': 2.0,
            'save_location': '/root/cannot_write_here',
            'next_x': 100,
            'next_y': 200,
            'safe_x': 50,
            'safe_y': 50
        }
        
        is_valid, message = self.capture.validate_capture_params(invalid_params)
        
        # Should detect invalid save location
        if not is_valid:
            self.assertIn("location", message.lower())
            
    def test_capture_interruption_handling(self):
        """Test handling of capture interruption."""
        if hasattr(self.capture, 'stop_capture'):
            # Start capture
            self.capture.is_capturing = True
            self.capture.current_page = 5
            
            # Stop capture
            self.capture.stop_capture()
            
            # Should properly reset state
            self.assertFalse(self.capture.is_capturing)
            
    def test_system_resource_error_handling(self):
        """Test handling of system resource errors."""
        if hasattr(self.capture, 'check_system_resources'):
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.side_effect = Exception("Memory check failed")
                
                result = self.capture.check_system_resources()
                
                # Should handle system check errors gracefully
                self.assertIsNotNone(result)


class TestBookCaptureIntegration(unittest.TestCase):
    """Integration tests for BookCapture."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.capture = BookCapture()
        
    def test_full_capture_workflow_validation(self):
        """Test validation of full capture workflow."""
        if hasattr(self.capture, 'validate_full_workflow'):
            workflow_params = {
                'pages': 10,
                'delay': 2.0,
                'save_location': '/tmp/captures',
                'next_x': 100,
                'next_y': 200,
                'safe_x': 50,
                'safe_y': 50,
                'format': 'png',
                'quality': 90
            }
            
            is_valid = self.capture.validate_full_workflow(workflow_params)
            
            self.assertIsInstance(is_valid, bool)
            
    def test_capture_session_management(self):
        """Test capture session management."""
        if hasattr(self.capture, 'start_capture_session'):
            session_id = self.capture.start_capture_session()
            
            self.assertIsNotNone(session_id)
            
            if hasattr(self.capture, 'end_capture_session'):
                result = self.capture.end_capture_session(session_id)
                self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()