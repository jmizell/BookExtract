"""
Book page capture functionality - handles automated screenshot capture and navigation.

This module provides the core capture functionality that can be used by GUI or CLI interfaces.
"""

import subprocess
import time
from pathlib import Path
from typing import Callable, Optional, Dict, Any


class BookCapture:
    """Handles automated book page capture with mouse navigation."""
    
    def __init__(self):
        """Initialize the capture handler."""
        self.is_capturing = False
        self.current_page = 0
        self.total_pages = 0
        
        # Callback functions for progress updates
        self.progress_callback: Optional[Callable[[int, str], None]] = None
        self.log_callback: Optional[Callable[[str], None]] = None
        self.completion_callback: Optional[Callable[[bool, str], None]] = None
        
    def set_callbacks(self, 
                     progress_callback: Optional[Callable[[int, str], None]] = None,
                     log_callback: Optional[Callable[[str], None]] = None,
                     completion_callback: Optional[Callable[[bool, str], None]] = None):
        """Set callback functions for progress updates and logging.
        
        Args:
            progress_callback: Called with (current_page, status_message)
            log_callback: Called with log messages
            completion_callback: Called with (success, message) when capture completes
        """
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.completion_callback = completion_callback
        
    def _log(self, message: str):
        """Internal logging method."""
        if self.log_callback:
            self.log_callback(message)
            
    def _update_progress(self, current: int, status: str):
        """Internal progress update method."""
        if self.progress_callback:
            self.progress_callback(current, status)
            
    def _notify_completion(self, success: bool, message: str):
        """Internal completion notification method."""
        if self.completion_callback:
            self.completion_callback(success, message)
    
    def check_dependencies(self) -> tuple[bool, list[str]]:
        """Check if required system tools are available.
        
        Returns:
            Tuple of (all_available, missing_tools)
        """
        required_tools = ['import', 'xdotool']
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
                
        return len(missing_tools) == 0, missing_tools
    
    def get_dependency_status(self) -> Dict[str, bool]:
        """Get detailed dependency status.
        
        Returns:
            Dictionary mapping tool names to availability status
        """
        tools = {
            'ImageMagick (import)': 'import',
            'xdotool': 'xdotool'
        }
        
        status = {}
        for name, command in tools.items():
            try:
                subprocess.run([command, '--version'], capture_output=True, check=True)
                status[name] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                status[name] = False
                
        return status
    
    def validate_capture_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Validate capture parameters.
        
        Args:
            params: Dictionary with keys: pages, delay, save_location, 
                   next_x, next_y, safe_x, safe_y
                   
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate pages
            pages = int(params.get('pages', 0))
            if pages <= 0:
                return False, "Number of pages must be positive"
                
            # Validate delay
            delay = float(params.get('delay', 0))
            if delay < 0:
                return False, "Delay must be non-negative"
                
            # Validate save location
            save_location = str(params.get('save_location', '')).strip()
            if not save_location:
                return False, "Save location must be specified"
                
            # Validate coordinates
            for coord in ['next_x', 'next_y', 'safe_x', 'safe_y']:
                try:
                    int(params.get(coord, 0))
                except (ValueError, TypeError):
                    return False, f"Invalid coordinate: {coord} must be an integer"
                    
        except (ValueError, TypeError) as e:
            return False, f"Invalid parameter: {e}"
            
        return True, ""
    
    def test_coordinates(self, next_x: int, next_y: int, safe_x: int, safe_y: int) -> tuple[bool, str]:
        """Test mouse coordinates by moving to each position.
        
        Args:
            next_x, next_y: Next button coordinates
            safe_x, safe_y: Safe area coordinates
            
        Returns:
            Tuple of (success, error_message)
        """
        # Check dependencies first
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            return False, f"Missing dependencies: {', '.join(missing)}"
            
        self._log("Testing coordinates...")
        
        try:
            # Move to next button position
            self._log(f"Moving to next button position: ({next_x}, {next_y})")
            subprocess.run(['xdotool', 'mousemove', str(next_x), str(next_y)], 
                         check=True, capture_output=True)
            time.sleep(1)
            
            # Move to safe area
            self._log(f"Moving to safe area: ({safe_x}, {safe_y})")
            subprocess.run(['xdotool', 'mousemove', str(safe_x), str(safe_y)], 
                         check=True, capture_output=True)
            
            self._log("Coordinate test completed successfully!")
            return True, "Test completed successfully"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Could not move mouse: {e}"
            self._log(f"Error testing coordinates: {e}")
            return False, error_msg
    
    def start_capture(self, params: Dict[str, Any]) -> bool:
        """Start the capture process.
        
        Args:
            params: Dictionary with capture parameters
            
        Returns:
            True if capture started successfully, False otherwise
        """
        # Validate parameters
        valid, error = self.validate_capture_params(params)
        if not valid:
            self._log(f"Invalid parameters: {error}")
            return False
            
        # Check dependencies
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            self._log(f"Missing dependencies: {', '.join(missing)}")
            return False
            
        # Create save directory
        save_location = Path(params['save_location'])
        try:
            save_location.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._log(f"Could not create directory: {e}")
            return False
            
        # Set up capture state
        self.is_capturing = True
        self.current_page = 0
        self.total_pages = int(params['pages'])
        
        # Start capture process
        self._capture_pages(params)
        return True
    
    def _capture_pages(self, params: Dict[str, Any]):
        """Internal method to capture pages."""
        try:
            total_pages = int(params['pages'])
            delay = float(params['delay'])
            save_location = Path(params['save_location'])
            
            next_x = int(params['next_x'])
            next_y = int(params['next_y'])
            safe_x = int(params['safe_x'])
            safe_y = int(params['safe_y'])
            
            self._log(f"Starting capture of {total_pages} pages...")
            
            for i in range(total_pages):
                if not self.is_capturing:
                    break
                    
                self.current_page = i
                page_num = f"{i:03d}"
                filename = save_location / f"page{page_num}.png"
                
                # Update progress
                self._update_progress(i, f"Capturing page {i+1}/{total_pages}")
                
                try:
                    # Take screenshot
                    subprocess.run(['import', '-window', 'root', str(filename)], 
                                 check=True, capture_output=True)
                    
                    # Move mouse to next button and click
                    subprocess.run(['xdotool', 'mousemove', str(next_x), str(next_y)], 
                                 check=True, capture_output=True)
                    subprocess.run(['xdotool', 'click', '1'], 
                                 check=True, capture_output=True)
                    
                    # Move mouse to safe area and click
                    subprocess.run(['xdotool', 'mousemove', str(safe_x), str(safe_y)], 
                                 check=True, capture_output=True)
                    subprocess.run(['xdotool', 'click', '1'], 
                                 check=True, capture_output=True)
                    
                    # Wait before next capture
                    time.sleep(delay)
                    
                except subprocess.CalledProcessError as e:
                    self._log(f"Error capturing page {i+1}: {e}")
                    self._notify_completion(False, f"Capture failed at page {i+1}: {e}")
                    return
                    
            # Capture completed or cancelled
            if self.is_capturing:
                self._log(f"Capture completed successfully! {total_pages} pages saved to {save_location}")
                self._notify_completion(True, f"Completed! Captured {total_pages} pages")
            else:
                self._log(f"Capture cancelled by user after {self.current_page} pages")
                self._notify_completion(False, f"Cancelled after {self.current_page} pages")
                
        except Exception as e:
            self._log(f"Unexpected error: {e}")
            self._notify_completion(False, f"Unexpected error: {e}")
        finally:
            self.is_capturing = False
    
    def cancel_capture(self):
        """Cancel the ongoing capture process."""
        if self.is_capturing:
            self.is_capturing = False
            self._log("Cancelling capture...")
    
    def get_capture_status(self) -> Dict[str, Any]:
        """Get current capture status.
        
        Returns:
            Dictionary with current status information
        """
        return {
            'is_capturing': self.is_capturing,
            'current_page': self.current_page,
            'total_pages': self.total_pages,
            'progress_percent': (self.current_page / self.total_pages * 100) if self.total_pages > 0 else 0
        }