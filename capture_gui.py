#!/usr/bin/env python3
"""
GUI version of capture.sh - A tkinter interface for automated book page capture.

This application provides a user-friendly interface to capture screenshots
of book pages with automated navigation between pages.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import time
import os
from pathlib import Path


class CaptureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Page Capture Tool")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # State variables
        self.is_capturing = False
        self.capture_thread = None
        self.current_page = 0
        
        # Default values
        self.default_save_location = str(Path.cwd() / "images")
        
        self.setup_ui()
        
    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Reset to Defaults", command=self.reset_defaults)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test Coordinates", command=self.test_coordinates, accelerator="Ctrl+T")
        tools_menu.add_command(label="Check Dependencies", command=self.show_dependency_status)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Usage Tips", command=self.show_usage_tips)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-t>', lambda e: self.test_coordinates())
        
    def setup_ui(self):
        """Create and layout the user interface."""
        # Create menu bar
        self.create_menu()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Book Page Capture Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Number of screenshots
        ttk.Label(main_frame, text="Number of pages:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.pages_var = tk.StringVar(value="380")
        pages_spinbox = ttk.Spinbox(main_frame, from_=1, to=9999, width=10, 
                                   textvariable=self.pages_var)
        pages_spinbox.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Delay between captures
        ttk.Label(main_frame, text="Delay (seconds):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.delay_var = tk.StringVar(value="0.5")
        delay_spinbox = ttk.Spinbox(main_frame, from_=0.1, to=10.0, increment=0.1, 
                                   width=10, textvariable=self.delay_var)
        delay_spinbox.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Save location
        ttk.Label(main_frame, text="Save location:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.location_var = tk.StringVar(value=self.default_save_location)
        location_entry = ttk.Entry(main_frame, textvariable=self.location_var)
        location_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        browse_button = ttk.Button(main_frame, text="Browse", command=self.browse_location)
        browse_button.grid(row=3, column=2, padx=(5, 0), pady=5)
        
        # Mouse coordinates section
        coords_frame = ttk.LabelFrame(main_frame, text="Mouse Coordinates", padding="10")
        coords_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 10))
        coords_frame.columnconfigure(1, weight=1)
        coords_frame.columnconfigure(3, weight=1)
        
        ttk.Label(coords_frame, text="Next button X:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.next_x_var = tk.StringVar(value="1865")
        ttk.Entry(coords_frame, textvariable=self.next_x_var, width=8).grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
        
        ttk.Label(coords_frame, text="Y:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.next_y_var = tk.StringVar(value="650")
        ttk.Entry(coords_frame, textvariable=self.next_y_var, width=8).grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(coords_frame, text="Safe area X:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.safe_x_var = tk.StringVar(value="30")
        ttk.Entry(coords_frame, textvariable=self.safe_x_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=(5, 10))
        
        ttk.Label(coords_frame, text="Y:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.safe_y_var = tk.StringVar(value="650")
        ttk.Entry(coords_frame, textvariable=self.safe_y_var, width=8).grid(row=1, column=3, sticky=tk.W, padx=(5, 0))
        
        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to capture")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(20, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Capture", 
                                      command=self.start_capture)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", 
                                       command=self.cancel_capture, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_coords_button = ttk.Button(button_frame, text="Test Coordinates", 
                                           command=self.test_coordinates)
        self.test_coords_button.pack(side=tk.LEFT)
        
        # Status text area
        status_frame = ttk.LabelFrame(main_frame, text="Status Log", padding="5")
        status_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.status_text = tk.Text(status_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Initial status message
        self.log_message("Application started. Configure settings and click 'Start Capture' to begin.")
        
    def browse_location(self):
        """Open a directory browser to select save location."""
        directory = filedialog.askdirectory(
            title="Select directory to save screenshots",
            initialdir=self.location_var.get()
        )
        if directory:
            self.location_var.set(directory)
            
    def log_message(self, message):
        """Add a message to the status log."""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def validate_inputs(self):
        """Validate user inputs before starting capture."""
        try:
            pages = int(self.pages_var.get())
            if pages <= 0:
                raise ValueError("Number of pages must be positive")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of pages (positive integer)")
            return False
            
        try:
            delay = float(self.delay_var.get())
            if delay < 0:
                raise ValueError("Delay must be non-negative")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid delay (non-negative number)")
            return False
            
        save_location = self.location_var.get().strip()
        if not save_location:
            messagebox.showerror("Invalid Input", "Please specify a save location")
            return False
            
        # Validate coordinates
        try:
            int(self.next_x_var.get())
            int(self.next_y_var.get())
            int(self.safe_x_var.get())
            int(self.safe_y_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid coordinates (integers)")
            return False
            
        return True
        
    def check_dependencies(self):
        """Check if required system tools are available."""
        required_tools = ['import', 'xdotool']
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
                
        if missing_tools:
            messagebox.showerror(
                "Missing Dependencies", 
                f"The following required tools are not installed:\n{', '.join(missing_tools)}\n\n"
                "Please install them using:\nsudo apt-get install imagemagick xdotool"
            )
            return False
            
        return True
        
    def start_capture(self):
        """Start the capture process."""
        if not self.validate_inputs() or not self.check_dependencies():
            return
            
        # Create save directory if it doesn't exist
        save_location = Path(self.location_var.get())
        try:
            save_location.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Directory Error", f"Could not create directory:\n{e}")
            return
            
        # Update UI state
        self.is_capturing = True
        self.current_page = 0
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # Setup progress bar
        total_pages = int(self.pages_var.get())
        self.progress_bar.config(maximum=total_pages, value=0)
        
        # Start capture in separate thread
        self.capture_thread = threading.Thread(target=self.capture_worker, daemon=True)
        self.capture_thread.start()
        
        self.log_message(f"Starting capture of {total_pages} pages...")
        
    def capture_worker(self):
        """Worker thread for the capture process."""
        try:
            total_pages = int(self.pages_var.get())
            delay = float(self.delay_var.get())
            save_location = Path(self.location_var.get())
            
            next_x = int(self.next_x_var.get())
            next_y = int(self.next_y_var.get())
            safe_x = int(self.safe_x_var.get())
            safe_y = int(self.safe_y_var.get())
            
            for i in range(total_pages):
                if not self.is_capturing:
                    break
                    
                self.current_page = i
                page_num = f"{i:03d}"
                filename = save_location / f"page{page_num}.png"
                
                # Update progress
                self.root.after(0, self.update_progress, i, f"Capturing page {i+1}/{total_pages}")
                
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
                    self.root.after(0, self.log_message, f"Error capturing page {i+1}: {e}")
                    break
                    
            # Capture completed or cancelled
            if self.is_capturing:
                self.root.after(0, self.capture_completed, total_pages)
            else:
                self.root.after(0, self.capture_cancelled)
                
        except Exception as e:
            self.root.after(0, self.log_message, f"Unexpected error: {e}")
            self.root.after(0, self.capture_cancelled)
            
    def update_progress(self, current, status):
        """Update progress bar and status."""
        self.progress_bar.config(value=current)
        self.progress_var.set(status)
        
    def capture_completed(self, total_pages):
        """Handle successful completion of capture."""
        self.is_capturing = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set(f"Completed! Captured {total_pages} pages")
        self.progress_bar.config(value=total_pages)
        self.log_message(f"Capture completed successfully! {total_pages} pages saved to {self.location_var.get()}")
        
    def test_coordinates(self):
        """Test the mouse coordinates by moving to each position."""
        try:
            next_x = int(self.next_x_var.get())
            next_y = int(self.next_y_var.get())
            safe_x = int(self.safe_x_var.get())
            safe_y = int(self.safe_y_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid coordinates (integers)")
            return
            
        if not self.check_dependencies():
            return
            
        self.log_message("Testing coordinates...")
        
        try:
            # Move to next button position
            self.log_message(f"Moving to next button position: ({next_x}, {next_y})")
            subprocess.run(['xdotool', 'mousemove', str(next_x), str(next_y)], 
                         check=True, capture_output=True)
            time.sleep(1)
            
            # Move to safe area
            self.log_message(f"Moving to safe area: ({safe_x}, {safe_y})")
            subprocess.run(['xdotool', 'mousemove', str(safe_x), str(safe_y)], 
                         check=True, capture_output=True)
            
            self.log_message("Coordinate test completed successfully!")
            messagebox.showinfo("Test Complete", 
                              "Mouse moved to both positions. Check if the positions are correct.")
            
        except subprocess.CalledProcessError as e:
            self.log_message(f"Error testing coordinates: {e}")
            messagebox.showerror("Test Failed", f"Could not move mouse: {e}")
    
    def cancel_capture(self):
        """Cancel the ongoing capture process."""
        if self.is_capturing:
            self.is_capturing = False
            self.log_message("Cancelling capture...")
            
    def capture_cancelled(self):
        """Handle cancelled capture."""
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set(f"Cancelled after {self.current_page} pages")
        self.log_message(f"Capture cancelled by user after {self.current_page} pages")
    
    def reset_defaults(self):
        """Reset all settings to default values."""
        self.pages_var.set("380")
        self.delay_var.set("0.5")
        self.location_var.set(self.default_save_location)
        self.next_x_var.set("1865")
        self.next_y_var.set("650")
        self.safe_x_var.set("30")
        self.safe_y_var.set("650")
        self.log_message("Settings reset to defaults")
        
    def show_dependency_status(self):
        """Show the status of required dependencies."""
        required_tools = [
            ('ImageMagick (import)', 'import'),
            ('xdotool', 'xdotool')
        ]
        
        status_lines = ["Dependency Status:\n"]
        all_good = True
        
        for name, command in required_tools:
            try:
                subprocess.run([command, '--version'], capture_output=True, check=True)
                status_lines.append(f"✓ {name}: Available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                status_lines.append(f"✗ {name}: Not found")
                all_good = False
        
        if all_good:
            status_lines.append("\nAll dependencies are available!")
        else:
            status_lines.append("\nSome dependencies are missing.")
            status_lines.append("Install with: sudo apt-get install imagemagick xdotool")
        
        messagebox.showinfo("Dependency Status", "\n".join(status_lines))
        
    def show_about(self):
        """Show about dialog."""
        about_text = """Book Page Capture GUI v1.0

A user-friendly interface for automated book page capture.

This application replaces the command-line capture.sh script 
with an intuitive graphical interface.

Features:
• Configurable capture settings
• Real-time progress tracking
• Coordinate testing
• Comprehensive error handling
• Status logging

Part of the BookExtract project.
Licensed under GPL v3.0"""
        
        messagebox.showinfo("About", about_text)
        
    def show_usage_tips(self):
        """Show usage tips dialog."""
        tips_text = """Usage Tips:

1. Setup your book viewer first:
   • Open book in full-screen mode
   • Navigate to first page to capture
   • Note the "next page" button position

2. Test coordinates before capturing:
   • Use Tools → Test Coordinates
   • Adjust coordinates if needed

3. Start with small tests:
   • Try 5-10 pages first
   • Verify everything works correctly

4. Optimal settings:
   • Use 0.5-1.0 second delay
   • Increase delay for slow-loading pages

5. Troubleshooting:
   • Ensure book viewer is visible
   • Check that coordinates are accurate
   • Verify dependencies are installed

Press Ctrl+T to test coordinates
Press Ctrl+Q to quit"""
        
        messagebox.showinfo("Usage Tips", tips_text)


def main():
    """Main application entry point."""
    root = tk.Tk()
    
    # Set up modern styling
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    app = CaptureGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.is_capturing:
            if messagebox.askokcancel("Quit", "Capture is in progress. Do you want to quit?"):
                app.is_capturing = False
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()