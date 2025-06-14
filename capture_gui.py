#!/usr/bin/env python3
"""
GUI version of capture.sh - A tkinter interface for automated book page capture.

This application provides a user-friendly interface to capture screenshots
of book pages with automated navigation between pages.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
from pathlib import Path
from book_capture import BookCapture


class CaptureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Page Capture Tool")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # Initialize capture handler
        self.capture_handler = BookCapture()
        self.capture_handler.set_callbacks(
            progress_callback=self.update_progress,
            log_callback=self.log_message,
            completion_callback=self.on_capture_complete
        )
        
        # State variables
        self.capture_thread = None
        
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
        
    def get_capture_params(self):
        """Get capture parameters from GUI inputs."""
        return {
            'pages': self.pages_var.get(),
            'delay': self.delay_var.get(),
            'save_location': self.location_var.get(),
            'next_x': self.next_x_var.get(),
            'next_y': self.next_y_var.get(),
            'safe_x': self.safe_x_var.get(),
            'safe_y': self.safe_y_var.get()
        }
        
    def start_capture(self):
        """Start the capture process."""
        # Get parameters from GUI
        params = self.get_capture_params()
        
        # Validate parameters using capture handler
        valid, error = self.capture_handler.validate_capture_params(params)
        if not valid:
            messagebox.showerror("Invalid Input", error)
            return
            
        # Check dependencies
        deps_ok, missing = self.capture_handler.check_dependencies()
        if not deps_ok:
            messagebox.showerror(
                "Missing Dependencies", 
                f"The following required tools are not installed:\n{', '.join(missing)}\n\n"
                "Please install them using:\nsudo apt-get install imagemagick xdotool"
            )
            return
            
        # Update UI state
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # Setup progress bar
        total_pages = int(params['pages'])
        self.progress_bar.config(maximum=total_pages, value=0)
        
        # Start capture in separate thread
        self.capture_thread = threading.Thread(target=self.capture_worker, args=(params,), daemon=True)
        self.capture_thread.start()
        
    def capture_worker(self, params):
        """Worker thread for the capture process."""
        self.capture_handler.start_capture(params)
            
    def update_progress(self, current, status):
        """Update progress bar and status (called from capture handler)."""
        # Use root.after to ensure thread safety
        self.root.after(0, self._update_progress_ui, current, status)
        
    def _update_progress_ui(self, current, status):
        """Internal method to update progress UI elements."""
        self.progress_bar.config(value=current)
        self.progress_var.set(status)
        
    def on_capture_complete(self, success, message):
        """Handle capture completion (called from capture handler)."""
        # Use root.after to ensure thread safety
        self.root.after(0, self._handle_completion_ui, success, message)
        
    def _handle_completion_ui(self, success, message):
        """Internal method to handle completion UI updates."""
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set(message)
        
        if success:
            # Set progress bar to maximum
            total_pages = int(self.pages_var.get())
            self.progress_bar.config(value=total_pages)
        
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
            
        # Use capture handler to test coordinates
        success, message = self.capture_handler.test_coordinates(next_x, next_y, safe_x, safe_y)
        
        if success:
            messagebox.showinfo("Test Complete", 
                              "Mouse moved to both positions. Check if the positions are correct.")
        else:
            messagebox.showerror("Test Failed", message)
    
    def cancel_capture(self):
        """Cancel the ongoing capture process."""
        self.capture_handler.cancel_capture()
    
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
        status_dict = self.capture_handler.get_dependency_status()
        
        status_lines = ["Dependency Status:\n"]
        all_good = True
        
        for name, available in status_dict.items():
            if available:
                status_lines.append(f"✓ {name}: Available")
            else:
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
        if app.capture_handler.is_capturing:
            if messagebox.askokcancel("Quit", "Capture is in progress. Do you want to quit?"):
                app.capture_handler.cancel_capture()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()