#!/usr/bin/env python3
"""
Unified Book Capture and Crop Tool - A tkinter interface combining capture and crop functionality.

This application provides a unified interface to capture book pages and crop them
in a single workflow, eliminating the need for separate capture and crop steps.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import subprocess
from pathlib import Path
from PIL import Image, ImageTk
from bookextract import BookCapture, ImageProcessor


class UnifiedBookTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified Book Capture & Crop Tool")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Initialize handlers
        self.capture_handler = BookCapture()
        self.capture_handler.set_callbacks(
            progress_callback=self.update_progress,
            log_callback=self.log_message,
            completion_callback=self.on_capture_complete
        )
        
        # State variables
        self.capture_thread = None
        self.preview_image = None
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_end_x = None
        self.crop_end_y = None
        self.crop_rect_id = None
        self.scale_factor = 1.0
        self.current_preview_path = None
        
        # Default values
        self.default_output_folder = str(Path.cwd() / "out")
        
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
        tools_menu.add_command(label="Take Test Screenshot", command=self.take_test_screenshot, accelerator="Ctrl+S")
        tools_menu.add_command(label="Check Dependencies", command=self.show_dependency_status)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Usage Tips", command=self.show_usage_tips)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-t>', lambda e: self.test_coordinates())
        self.root.bind('<Control-s>', lambda e: self.take_test_screenshot())
        
    def setup_ui(self):
        """Create and layout the user interface."""
        # Create menu bar
        self.create_menu()
        
        # Main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls
        left_frame = ttk.Frame(main_paned, padding="10")
        main_paned.add(left_frame, weight=1)
        
        # Right panel for preview
        right_frame = ttk.Frame(main_paned, padding="10")
        main_paned.add(right_frame, weight=2)
        
        self.setup_controls(left_frame)
        self.setup_preview(right_frame)
        
    def setup_controls(self, parent):
        """Setup the control panel."""
        # Title
        title_label = ttk.Label(parent, text="Unified Book Capture & Crop Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Capture Settings Section
        capture_frame = ttk.LabelFrame(parent, text="Capture Settings", padding="10")
        capture_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        capture_frame.columnconfigure(1, weight=1)
        
        # Number of pages
        ttk.Label(capture_frame, text="Number of pages:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.pages_var = tk.StringVar(value="380")
        pages_spinbox = ttk.Spinbox(capture_frame, from_=1, to=9999, width=10, 
                                   textvariable=self.pages_var)
        pages_spinbox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Initial sequence number
        ttk.Label(capture_frame, text="Initial sequence number:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.initial_seq_var = tk.StringVar(value="0")
        seq_spinbox = ttk.Spinbox(capture_frame, from_=0, to=9999, width=10, 
                                 textvariable=self.initial_seq_var)
        seq_spinbox.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Delay between captures
        ttk.Label(capture_frame, text="Delay (seconds):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.delay_var = tk.StringVar(value="0.5")
        delay_spinbox = ttk.Spinbox(capture_frame, from_=0.1, to=10.0, increment=0.1, 
                                   width=10, textvariable=self.delay_var)
        delay_spinbox.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Output folder
        ttk.Label(capture_frame, text="Output folder:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.output_folder_var = tk.StringVar(value=self.default_output_folder)
        output_entry = ttk.Entry(capture_frame, textvariable=self.output_folder_var)
        output_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        output_browse_button = ttk.Button(capture_frame, text="Browse", 
                                         command=self.browse_output_folder)
        output_browse_button.grid(row=3, column=2, padx=(5, 0), pady=2)
        
        # Mouse coordinates section
        coords_frame = ttk.LabelFrame(parent, text="Mouse Coordinates", padding="10")
        coords_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
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
        
        # Crop coordinates section
        crop_frame = ttk.LabelFrame(parent, text="Crop Coordinates", padding="10")
        crop_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        crop_frame.columnconfigure(1, weight=1)
        crop_frame.columnconfigure(3, weight=1)
        
        ttk.Label(crop_frame, text="X:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.crop_x_var = tk.StringVar(value="1056")
        ttk.Entry(crop_frame, textvariable=self.crop_x_var, width=8).grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
        
        ttk.Label(crop_frame, text="Y:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.crop_y_var = tk.StringVar(value="190")
        ttk.Entry(crop_frame, textvariable=self.crop_y_var, width=8).grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(crop_frame, text="Width:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.crop_width_var = tk.StringVar(value="822")
        ttk.Entry(crop_frame, textvariable=self.crop_width_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=(5, 10))
        
        ttk.Label(crop_frame, text="Height:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.crop_height_var = tk.StringVar(value="947")
        ttk.Entry(crop_frame, textvariable=self.crop_height_var, width=8).grid(row=1, column=3, sticky=tk.W, padx=(5, 0))
        
        # Progress section
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to capture")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(20, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Capture & Crop", 
                                      command=self.start_capture)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", 
                                       command=self.cancel_capture, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_coords_button = ttk.Button(button_frame, text="Test Coordinates", 
                                           command=self.test_coordinates)
        self.test_coords_button.pack(side=tk.LEFT)
        
        # Status text area
        status_frame = ttk.LabelFrame(parent, text="Status Log", padding="5")
        status_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(6, weight=1)
        
        self.status_text = tk.Text(status_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        parent.columnconfigure(1, weight=1)
        
        # Initial status message
        self.log_message("Application started. Configure settings and click 'Start Capture & Crop' to begin.")
        
    def setup_preview(self, parent):
        """Setup the image preview panel."""
        # Preview title
        preview_title = ttk.Label(parent, text="Image Preview", 
                                 font=("Arial", 14, "bold"))
        preview_title.pack(pady=(0, 10))
        
        # Instructions and refresh button
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(pady=(0, 10))
        
        instructions = ttk.Label(controls_frame, 
                                text="Click and drag to select crop area")
        instructions.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_button = ttk.Button(controls_frame, text="Refresh Preview", 
                                        command=self.refresh_preview)
        self.refresh_button.pack(side=tk.RIGHT)
        
        # Canvas for image preview
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_canvas = tk.Canvas(canvas_frame, bg='white', cursor='crosshair')
        
        # Scrollbars for canvas
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)
        self.preview_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for canvas and scrollbars
        self.preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        # Bind mouse events for crop selection
        self.preview_canvas.bind("<Button-1>", self.start_crop_selection)
        self.preview_canvas.bind("<B1-Motion>", self.update_crop_selection)
        self.preview_canvas.bind("<ButtonRelease-1>", self.end_crop_selection)
        
        # Bind coordinate field changes to update preview
        for var in [self.crop_x_var, self.crop_y_var, self.crop_width_var, self.crop_height_var]:
            var.trace('w', lambda *args: self.update_crop_preview())
        
    def browse_output_folder(self):
        """Open a directory browser to select output folder."""
        directory = filedialog.askdirectory(
            title="Select output folder for captured and cropped images",
            initialdir=self.output_folder_var.get()
        )
        if directory:
            self.output_folder_var.set(directory)
            
    def log_message(self, message):
        """Add a message to the status log."""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def take_test_screenshot(self):
        """Take a test screenshot for preview."""
        try:
            output_dir = Path(self.output_folder_var.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            temp_path = output_dir / "preview.png"
            
            # Take screenshot
            subprocess.run(['import', '-window', 'root', str(temp_path)], 
                         check=True, capture_output=True)
            
            self.current_preview_path = temp_path
            self.load_preview_image()
            self.log_message("Test screenshot taken and loaded for preview")
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Screenshot Error", f"Could not take screenshot: {e}")
            self.log_message(f"Error taking screenshot: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")
            self.log_message(f"Unexpected error: {e}")
            
    def refresh_preview(self):
        """Refresh the preview image."""
        if self.current_preview_path and self.current_preview_path.exists():
            self.load_preview_image()
            self.log_message("Preview refreshed")
        else:
            self.take_test_screenshot()
            
    def load_preview_image(self):
        """Load and display the preview image."""
        if not self.current_preview_path or not self.current_preview_path.exists():
            return
            
        try:
            # Load image
            image = Image.open(self.current_preview_path)
            
            # Calculate display size (max 600x400 while maintaining aspect ratio)
            max_width, max_height = 600, 400
            img_width, img_height = image.size
            
            self.scale_factor = min(max_width / img_width, max_height / img_height, 1.0)
            display_width = int(img_width * self.scale_factor)
            display_height = int(img_height * self.scale_factor)
            
            # Resize image for display
            display_image = image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for tkinter
            self.preview_image = ImageTk.PhotoImage(display_image)
            
            # Update canvas
            self.preview_canvas.delete("all")
            self.preview_canvas.config(scrollregion=(0, 0, display_width, display_height))
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_image)
            
            # Update crop preview
            self.update_crop_preview()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load preview image: {e}")
            self.log_message(f"Error loading preview: {e}")
            
    def start_crop_selection(self, event):
        """Start crop area selection."""
        if self.preview_image is None:
            return
            
        # Convert canvas coordinates to image coordinates
        canvas_x = self.preview_canvas.canvasx(event.x)
        canvas_y = self.preview_canvas.canvasy(event.y)
        
        self.crop_start_x = int(canvas_x / self.scale_factor)
        self.crop_start_y = int(canvas_y / self.scale_factor)
        
        # Remove existing crop rectangle
        if self.crop_rect_id:
            self.preview_canvas.delete(self.crop_rect_id)
            
    def update_crop_selection(self, event):
        """Update crop area selection."""
        if self.preview_image is None or self.crop_start_x is None:
            return
            
        # Convert canvas coordinates to image coordinates
        canvas_x = self.preview_canvas.canvasx(event.x)
        canvas_y = self.preview_canvas.canvasy(event.y)
        
        self.crop_end_x = int(canvas_x / self.scale_factor)
        self.crop_end_y = int(canvas_y / self.scale_factor)
        
        # Draw crop rectangle on canvas
        if self.crop_rect_id:
            self.preview_canvas.delete(self.crop_rect_id)
            
        # Convert back to canvas coordinates for drawing
        canvas_start_x = self.crop_start_x * self.scale_factor
        canvas_start_y = self.crop_start_y * self.scale_factor
        canvas_end_x = self.crop_end_x * self.scale_factor
        canvas_end_y = self.crop_end_y * self.scale_factor
        
        self.crop_rect_id = self.preview_canvas.create_rectangle(
            canvas_start_x, canvas_start_y, canvas_end_x, canvas_end_y,
            outline='red', width=2, dash=(5, 5)
        )
        
    def end_crop_selection(self, event):
        """End crop area selection and update coordinates."""
        if self.preview_image is None or self.crop_start_x is None:
            return
            
        # Ensure we have valid coordinates
        if self.crop_end_x is None or self.crop_end_y is None:
            return
            
        # Calculate crop parameters
        x = min(self.crop_start_x, self.crop_end_x)
        y = min(self.crop_start_y, self.crop_end_y)
        width = abs(self.crop_end_x - self.crop_start_x)
        height = abs(self.crop_end_y - self.crop_start_y)
        
        # Update coordinate fields
        self.crop_x_var.set(str(x))
        self.crop_y_var.set(str(y))
        self.crop_width_var.set(str(width))
        self.crop_height_var.set(str(height))
        
    def update_crop_preview(self):
        """Update the crop preview based on current coordinates."""
        if self.preview_image is None:
            return
            
        try:
            x = int(self.crop_x_var.get())
            y = int(self.crop_y_var.get())
            width = int(self.crop_width_var.get())
            height = int(self.crop_height_var.get())
            
            # Remove existing crop rectangle
            if self.crop_rect_id:
                self.preview_canvas.delete(self.crop_rect_id)
                
            # Convert to canvas coordinates
            canvas_x = x * self.scale_factor
            canvas_y = y * self.scale_factor
            canvas_width = width * self.scale_factor
            canvas_height = height * self.scale_factor
            
            # Draw crop rectangle
            self.crop_rect_id = self.preview_canvas.create_rectangle(
                canvas_x, canvas_y, canvas_x + canvas_width, canvas_y + canvas_height,
                outline='red', width=2, dash=(5, 5)
            )
            
        except ValueError:
            # Invalid coordinates, ignore
            pass
            
    def get_capture_params(self):
        """Get capture parameters from GUI inputs."""
        return {
            'pages': self.pages_var.get(),
            'delay': self.delay_var.get(),
            'save_location': self.output_folder_var.get(),
            'next_x': self.next_x_var.get(),
            'next_y': self.next_y_var.get(),
            'safe_x': self.safe_x_var.get(),
            'safe_y': self.safe_y_var.get(),
            'initial_seq': self.initial_seq_var.get(),
            'crop_x': self.crop_x_var.get(),
            'crop_y': self.crop_y_var.get(),
            'crop_width': self.crop_width_var.get(),
            'crop_height': self.crop_height_var.get()
        }
        
    def validate_inputs(self):
        """Validate user inputs before processing."""
        params = self.get_capture_params()
        
        # Validate capture parameters
        valid, error = self.capture_handler.validate_capture_params(params)
        if not valid:
            messagebox.showerror("Invalid Input", error)
            return False
            
        # Validate crop coordinates
        try:
            x = int(params['crop_x'])
            y = int(params['crop_y'])
            width = int(params['crop_width'])
            height = int(params['crop_height'])
            
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                raise ValueError("Invalid crop dimensions")
                
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid crop coordinates (non-negative integers)")
            return False
            
        return True
        
    def start_capture(self):
        """Start the unified capture and crop process."""
        if not self.validate_inputs():
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
            
        # Check PIL dependency
        try:
            from PIL import Image
        except ImportError:
            messagebox.showerror(
                "Missing Dependencies", 
                "Pillow (PIL) is not available.\n\n"
                "Please install Pillow using:\npip install Pillow"
            )
            return
            
        # Update UI state
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # Setup progress bar
        params = self.get_capture_params()
        total_pages = int(params['pages'])
        self.progress_bar.config(maximum=total_pages, value=0)
        
        # Start capture in separate thread
        self.capture_thread = threading.Thread(target=self.capture_and_crop_worker, args=(params,), daemon=True)
        self.capture_thread.start()
        
    def capture_and_crop_worker(self, params):
        """Worker thread for the unified capture and crop process."""
        try:
            total_pages = int(params['pages'])
            delay = float(params['delay'])
            save_location = Path(params['save_location'])
            initial_seq = int(params['initial_seq'])
            
            next_x = int(params['next_x'])
            next_y = int(params['next_y'])
            safe_x = int(params['safe_x'])
            safe_y = int(params['safe_y'])
            
            crop_x = int(params['crop_x'])
            crop_y = int(params['crop_y'])
            crop_width = int(params['crop_width'])
            crop_height = int(params['crop_height'])
            
            # Create output directory
            save_location.mkdir(parents=True, exist_ok=True)

            # Set the capturing flag to True
            self.capture_handler.is_capturing = True
            self.capture_handler.total_pages = total_pages

            self.root.after(0, self.log_message, f"Starting unified capture and crop of {total_pages} pages...")

            self.log_message(f"Starting unified capture and crop of {total_pages} pages...")
            
            for i in range(total_pages):
                if not self.capture_handler.is_capturing:
                    break

                # Update current page tracking
                self.capture_handler.current_page = i

                page_num = f"{i + initial_seq:03d}"
                temp_filename = save_location / f"temp_page{page_num}.png"
                final_filename = save_location / f"page{page_num}.png"
                
                # Update progress
                self.root.after(0, self.update_progress, i, f"Capturing and cropping page {i+1}/{total_pages}")
                
                try:
                    # Take screenshot
                    subprocess.run(['import', '-window', 'root', str(temp_filename)], 
                                 check=True, capture_output=True)
                    
                    # Crop the image using PIL
                    with Image.open(temp_filename) as img:
                        # Define crop box (left, top, right, bottom)
                        crop_box = (crop_x, crop_y, crop_x + crop_width, crop_y + crop_height)
                        
                        # Ensure crop box is within image bounds
                        img_width, img_height = img.size
                        crop_box = (
                            max(0, min(crop_box[0], img_width)),
                            max(0, min(crop_box[1], img_height)),
                            max(0, min(crop_box[2], img_width)),
                            max(0, min(crop_box[3], img_height))
                        )
                        
                        # Crop and save the image
                        cropped_img = img.crop(crop_box)
                        cropped_img.save(final_filename)
                    
                    # Remove temporary file
                    temp_filename.unlink()
                    
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
                    self.root.after(0, self.on_capture_complete, False, f"Capture failed at page {i+1}: {e}")
                    return
                except Exception as e:
                    self.root.after(0, self.log_message, f"Error processing page {i+1}: {e}")
                    self.root.after(0, self.on_capture_complete, False, f"Processing failed at page {i+1}: {e}")
                    return
                    
            # Capture completed or cancelled
            if self.capture_handler.is_capturing:
                self.root.after(0, self.log_message, f"Unified capture and crop completed successfully! {total_pages} pages saved to {save_location}")
                self.root.after(0, self.on_capture_complete, True, f"Completed! Captured and cropped {total_pages} pages")
            else:
                self.root.after(0, self.log_message, f"Capture cancelled by user after {i} pages")
                self.root.after(0, self.on_capture_complete, False, f"Cancelled after {i} pages")
                
        except Exception as e:
            self.root.after(0, self.log_message, f"Unexpected error: {e}")
            self.root.after(0, self.on_capture_complete, False, f"Unexpected error: {e}")
        finally:
            self.capture_handler.is_capturing = False
            
    def update_progress(self, current, status):
        """Update progress bar and status (called from capture handler)."""
        self.progress_bar.config(value=current)
        self.progress_var.set(status)
        
    def on_capture_complete(self, success, message):
        """Handle capture completion."""
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set(message)
        
        if success:
            # Set progress bar to maximum
            total_pages = int(self.pages_var.get())
            # Update initial sequence number for next capture
            initial_seq = int(self.initial_seq_var.get())
            self.initial_seq_var.set(str(initial_seq + total_pages))
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
        self.initial_seq_var.set("0")
        self.delay_var.set("0.5")
        self.output_folder_var.set(self.default_output_folder)
        self.next_x_var.set("1865")
        self.next_y_var.set("650")
        self.safe_x_var.set("30")
        self.safe_y_var.set("650")
        self.crop_x_var.set("1056")
        self.crop_y_var.set("190")
        self.crop_width_var.set("822")
        self.crop_height_var.set("947")
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
        
        # Check PIL
        try:
            import PIL
            status_lines.append(f"✓ Pillow: Available (v{PIL.__version__})")
        except ImportError:
            status_lines.append("✗ Pillow: Not found")
            all_good = False
        
        if all_good:
            status_lines.append("\nAll dependencies are available!")
        else:
            status_lines.append("\nSome dependencies are missing.")
            status_lines.append("Install with: sudo apt-get install imagemagick xdotool")
            status_lines.append("Install Pillow with: pip install Pillow")
        
        messagebox.showinfo("Dependency Status", "\n".join(status_lines))
        
    def show_about(self):
        """Show about dialog."""
        about_text = """Unified Book Capture & Crop Tool v1.0

A unified interface combining book page capture and cropping functionality.

This application streamlines the book digitization workflow by capturing
and cropping pages in a single step, eliminating the need for separate
capture and crop operations.

Features:
• Automated page capture with mouse navigation
• Real-time crop coordinate selection with preview
• Configurable capture settings and sequence numbering
• Comprehensive error handling and progress tracking
• Status logging and coordinate testing
• Unified workflow for efficiency

Part of the BookExtract project.
Licensed under GPL v3.0"""
        
        messagebox.showinfo("About", about_text)
        
    def show_usage_tips(self):
        """Show usage tips dialog."""
        tips_text = """Usage Tips:

1. Setup your book viewer first:
   • Open book in full-screen mode
   • Navigate to first page to capture

2. Take a test screenshot:
   • Use Tools → Take Test Screenshot (Ctrl+S)
   • This loads a preview for crop selection

3. Set crop coordinates:
   • Click and drag on preview to select crop area
   • Or manually enter coordinates in the fields

4. Test coordinates before capturing:
   • Use Tools → Test Coordinates (Ctrl+T)
   • Adjust coordinates if needed

5. Configure capture settings:
   • Set number of pages and initial sequence number
   • Adjust delay for slow-loading pages

6. Start unified capture:
   • Click 'Start Capture & Crop'
   • Pages will be captured and cropped automatically

7. Troubleshooting:
   • Ensure book viewer is visible
   • Check that coordinates are accurate
   • Verify dependencies are installed

Keyboard shortcuts:
• Ctrl+S: Take test screenshot
• Ctrl+T: Test coordinates
• Ctrl+Q: Quit"""
        
        messagebox.showinfo("Usage Tips", tips_text)


def main():
    """Main application entry point."""
    root = tk.Tk()
    
    # Set up modern styling
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    app = UnifiedBookTool(root)
    
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