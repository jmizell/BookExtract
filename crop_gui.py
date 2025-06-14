#!/usr/bin/env python3
"""
GUI version of crop.sh - A tkinter interface for batch image cropping.

This application provides a user-friendly interface to crop multiple images
with preview functionality and mouse-based crop area selection. Uses Pillow
for image processing, eliminating the need for external dependencies.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw
import glob


class ImageProcessor:
    """Handles image loading, processing, and crop operations."""
    
    def __init__(self):
        self.image_files = []
        self.current_image_index = 0
        self.current_image = None
        
        # Default crop coordinates
        self.crop_x = 1056
        self.crop_y = 190
        self.crop_width = 822
        self.crop_height = 947
        
    def load_images_from_folder(self, input_folder):
        """Load images from the specified folder."""
        input_path = Path(input_folder)
        if not input_path.exists():
            raise FileNotFoundError(f"Input folder does not exist: {input_path}")
            
        # Find all image files
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff', '*.gif']
        self.image_files = []
        
        for ext in image_extensions:
            self.image_files.extend(glob.glob(str(input_path / ext)))
            self.image_files.extend(glob.glob(str(input_path / ext.upper())))
            
        if not self.image_files:
            raise ValueError(f"No image files found in {input_path}")
            
        self.image_files.sort()
        self.current_image_index = 0
        return len(self.image_files)
        
    def get_current_image_info(self):
        """Get information about the current image."""
        if not self.image_files:
            return None, "No images loaded"
            
        filename = Path(self.image_files[self.current_image_index]).name
        info = f"{self.current_image_index + 1}/{len(self.image_files)}: {filename}"
        return self.current_image_index, info
        
    def can_navigate_prev(self):
        """Check if we can navigate to previous image."""
        return self.current_image_index > 0
        
    def can_navigate_next(self):
        """Check if we can navigate to next image."""
        return self.current_image_index < len(self.image_files) - 1
        
    def navigate_prev(self):
        """Navigate to previous image."""
        if self.can_navigate_prev():
            self.current_image_index -= 1
            return True
        return False
        
    def navigate_next(self):
        """Navigate to next image."""
        if self.can_navigate_next():
            self.current_image_index += 1
            return True
        return False
        
    def load_current_image(self):
        """Load the current image and return it along with display info."""
        if not self.image_files:
            return None, None, None
            
        try:
            image_path = self.image_files[self.current_image_index]
            self.current_image = Image.open(image_path)
            
            # Calculate display size (max 600x400 while maintaining aspect ratio)
            max_width, max_height = 600, 400
            img_width, img_height = self.current_image.size
            
            scale = min(max_width / img_width, max_height / img_height, 1.0)
            display_width = int(img_width * scale)
            display_height = int(img_height * scale)
            
            # Resize image for display
            display_image = self.current_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            return self.current_image, display_image, scale
            
        except Exception as e:
            raise Exception(f"Could not load image: {e}")
            
    def set_crop_coordinates(self, x, y, width, height):
        """Set the crop coordinates."""
        self.crop_x = x
        self.crop_y = y
        self.crop_width = width
        self.crop_height = height
        
    def get_crop_coordinates(self):
        """Get the current crop coordinates."""
        return self.crop_x, self.crop_y, self.crop_width, self.crop_height
        
    def validate_crop_coordinates(self):
        """Validate crop coordinates."""
        if self.crop_x < 0 or self.crop_y < 0 or self.crop_width <= 0 or self.crop_height <= 0:
            raise ValueError("Invalid crop dimensions")
        return True
        
    def check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            from PIL import Image
            return True
        except ImportError:
            return False
            
    def process_images(self, output_folder, progress_callback=None):
        """Process all loaded images with the current crop settings."""
        if not self.image_files:
            raise ValueError("No images loaded")
            
        self.validate_crop_coordinates()
        
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        processed_count = 0
        
        for i, image_path in enumerate(self.image_files):
            if progress_callback:
                should_continue = progress_callback(i, f"Processing {i+1}/{len(self.image_files)}")
                if not should_continue:
                    break
                    
            try:
                input_path = Path(image_path)
                output_file = output_path / input_path.name
                
                # Use Pillow to crop the image
                with Image.open(input_path) as img:
                    # Define crop box (left, top, right, bottom)
                    crop_box = (self.crop_x, self.crop_y, 
                               self.crop_x + self.crop_width, 
                               self.crop_y + self.crop_height)
                    
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
                    cropped_img.save(output_file)
                    processed_count += 1
                
            except Exception as e:
                raise Exception(f"Error processing {input_path.name}: {e}")
                
        return processed_count


class CropGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Crop Tool")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Initialize image processor
        self.image_processor = ImageProcessor()
        
        # State variables for GUI
        self.is_processing = False
        self.process_thread = None
        self.preview_image = None
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_end_x = None
        self.crop_end_y = None
        self.crop_rect_id = None
        self.scale_factor = 1.0
        
        # Default values from crop.sh
        self.default_input_folder = str(Path.cwd() / "images")
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
        tools_menu.add_command(label="Check Dependencies", command=self.show_dependency_status)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Usage Tips", command=self.show_usage_tips)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
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
        title_label = ttk.Label(parent, text="Image Crop Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input folder
        ttk.Label(parent, text="Input folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.input_folder_var = tk.StringVar(value=self.default_input_folder)
        input_entry = ttk.Entry(parent, textvariable=self.input_folder_var, width=30)
        input_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        input_browse_button = ttk.Button(parent, text="Browse", 
                                        command=self.browse_input_folder)
        input_browse_button.grid(row=1, column=2, padx=(5, 0), pady=5)
        
        # Output folder
        ttk.Label(parent, text="Output folder:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_folder_var = tk.StringVar(value=self.default_output_folder)
        output_entry = ttk.Entry(parent, textvariable=self.output_folder_var, width=30)
        output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        output_browse_button = ttk.Button(parent, text="Browse", 
                                         command=self.browse_output_folder)
        output_browse_button.grid(row=2, column=2, padx=(5, 0), pady=5)
        
        # Crop coordinates section
        coords_frame = ttk.LabelFrame(parent, text="Crop Coordinates", padding="10")
        coords_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 10))
        coords_frame.columnconfigure(1, weight=1)
        
        ttk.Label(coords_frame, text="X:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.crop_x_var = tk.StringVar(value="1056")
        ttk.Entry(coords_frame, textvariable=self.crop_x_var, width=8).grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
        
        ttk.Label(coords_frame, text="Y:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.crop_y_var = tk.StringVar(value="190")
        ttk.Entry(coords_frame, textvariable=self.crop_y_var, width=8).grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(coords_frame, text="Width:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.crop_width_var = tk.StringVar(value="822")
        ttk.Entry(coords_frame, textvariable=self.crop_width_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=(5, 10))
        
        ttk.Label(coords_frame, text="Height:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.crop_height_var = tk.StringVar(value="947")
        ttk.Entry(coords_frame, textvariable=self.crop_height_var, width=8).grid(row=1, column=3, sticky=tk.W, padx=(5, 0))
        
        # Image navigation
        nav_frame = ttk.LabelFrame(parent, text="Image Navigation", padding="10")
        nav_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 10))
        
        self.prev_button = ttk.Button(nav_frame, text="Previous", 
                                     command=self.prev_image, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.image_info_var = tk.StringVar(value="No images loaded")
        ttk.Label(nav_frame, textvariable=self.image_info_var).pack(side=tk.LEFT, padx=10)
        
        self.next_button = ttk.Button(nav_frame, text="Next", 
                                     command=self.next_image, state=tk.DISABLED)
        self.next_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Load images button
        load_button = ttk.Button(parent, text="Load Images", command=self.load_images)
        load_button.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        # Progress section
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to process")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(20, 0))
        
        self.process_button = ttk.Button(button_frame, text="Process Images", 
                                        command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", 
                                       command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT)
        
        # Configure grid weights
        parent.columnconfigure(1, weight=1)
        
    def setup_preview(self, parent):
        """Setup the image preview panel."""
        # Preview title
        preview_title = ttk.Label(parent, text="Image Preview", 
                                 font=("Arial", 14, "bold"))
        preview_title.pack(pady=(0, 10))
        
        # Instructions
        instructions = ttk.Label(parent, 
                                text="Click and drag to select crop area\nUse navigation buttons to browse images",
                                justify=tk.CENTER)
        instructions.pack(pady=(0, 10))
        
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
        
    def browse_input_folder(self):
        """Open a directory browser to select input folder."""
        directory = filedialog.askdirectory(
            title="Select input folder containing images",
            initialdir=self.input_folder_var.get()
        )
        if directory:
            self.input_folder_var.set(directory)
            
    def browse_output_folder(self):
        """Open a directory browser to select output folder."""
        directory = filedialog.askdirectory(
            title="Select output folder for cropped images",
            initialdir=self.output_folder_var.get()
        )
        if directory:
            self.output_folder_var.set(directory)
            
    def load_images(self):
        """Load images from the input folder."""
        try:
            count = self.image_processor.load_images_from_folder(self.input_folder_var.get())
            
            # Update navigation
            self.update_navigation_buttons()
            self.load_current_image()
            
            messagebox.showinfo("Images Loaded", f"Loaded {count} images")
            
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
        except ValueError as e:
            messagebox.showwarning("No Images", str(e))
        
    def update_navigation_buttons(self):
        """Update the state of navigation buttons."""
        current_index, info = self.image_processor.get_current_image_info()
        
        if current_index is None:
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.image_info_var.set(info)
            return
            
        self.prev_button.config(state=tk.NORMAL if self.image_processor.can_navigate_prev() else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.image_processor.can_navigate_next() else tk.DISABLED)
        self.image_info_var.set(info)
        
    def prev_image(self):
        """Navigate to previous image."""
        if self.image_processor.navigate_prev():
            self.update_navigation_buttons()
            self.load_current_image()
            
    def next_image(self):
        """Navigate to next image."""
        if self.image_processor.navigate_next():
            self.update_navigation_buttons()
            self.load_current_image()
            
    def load_current_image(self):
        """Load and display the current image."""
        try:
            current_image, display_image, scale = self.image_processor.load_current_image()
            
            if current_image is None:
                return
                
            # Convert to PhotoImage for tkinter
            self.preview_image = ImageTk.PhotoImage(display_image)
            
            # Update canvas
            self.preview_canvas.delete("all")
            display_width, display_height = display_image.size
            self.preview_canvas.config(scrollregion=(0, 0, display_width, display_height))
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_image)
            
            # Store scale factor for coordinate conversion
            self.scale_factor = scale
            
            # Update crop coordinates from processor and draw preview
            self.sync_crop_coordinates_from_processor()
            self.update_crop_preview()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def sync_crop_coordinates_from_processor(self):
        """Sync crop coordinates from processor to GUI fields."""
        x, y, width, height = self.image_processor.get_crop_coordinates()
        self.crop_x_var.set(str(x))
        self.crop_y_var.set(str(y))
        self.crop_width_var.set(str(width))
        self.crop_height_var.set(str(height))
        
    def sync_crop_coordinates_to_processor(self):
        """Sync crop coordinates from GUI fields to processor."""
        try:
            x = int(self.crop_x_var.get())
            y = int(self.crop_y_var.get())
            width = int(self.crop_width_var.get())
            height = int(self.crop_height_var.get())
            self.image_processor.set_crop_coordinates(x, y, width, height)
        except ValueError:
            pass  # Invalid values, ignore
            
    def start_crop_selection(self, event):
        """Start crop area selection."""
        if self.image_processor.current_image is None:
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
        if self.image_processor.current_image is None or self.crop_start_x is None:
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
        if self.image_processor.current_image is None or self.crop_start_x is None:
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
        
        # Sync to processor
        self.image_processor.set_crop_coordinates(x, y, width, height)
        
    def update_crop_preview(self):
        """Update the crop preview based on current coordinates."""
        if self.image_processor.current_image is None:
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
            
    def validate_inputs(self):
        """Validate user inputs before processing."""
        input_folder = Path(self.input_folder_var.get())
        if not input_folder.exists():
            messagebox.showerror("Invalid Input", f"Input folder does not exist: {input_folder}")
            return False
            
        output_folder = self.output_folder_var.get().strip()
        if not output_folder:
            messagebox.showerror("Invalid Input", "Please specify an output folder")
            return False
            
        try:
            x = int(self.crop_x_var.get())
            y = int(self.crop_y_var.get())
            width = int(self.crop_width_var.get())
            height = int(self.crop_height_var.get())
            
            if x < 0 or y < 0 or width <= 0 or height <= 0:
                raise ValueError("Invalid crop dimensions")
                
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid crop coordinates (non-negative integers)")
            return False
            
        if not self.image_processor.image_files:
            messagebox.showerror("No Images", "Please load images first")
            return False
            
        return True
        
    def check_dependencies(self):
        """Check if Pillow is available."""
        if not self.image_processor.check_dependencies():
            messagebox.showerror(
                "Missing Dependencies", 
                "Pillow (PIL) is not available.\n\n"
                "Please install Pillow using:\npip install Pillow"
            )
            return False
        return True
            
    def start_processing(self):
        """Start the image processing."""
        if not self.validate_inputs() or not self.check_dependencies():
            return
            
        # Create output directory if it doesn't exist
        output_folder = Path(self.output_folder_var.get())
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Directory Error", f"Could not create output directory:\n{e}")
            return
            
        # Update UI state
        self.is_processing = True
        self.process_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # Sync coordinates to processor
        self.sync_crop_coordinates_to_processor()
        
        # Setup progress bar
        self.progress_bar.config(maximum=len(self.image_processor.image_files), value=0)
        
        # Start processing in separate thread
        self.process_thread = threading.Thread(target=self.process_worker, daemon=True)
        self.process_thread.start()
        
    def process_worker(self):
        """Worker thread for image processing."""
        def progress_callback(current, status):
            """Callback for progress updates."""
            if not self.is_processing:
                return False  # Signal to stop processing
            self.root.after(0, self.update_progress, current, status)
            return True  # Continue processing
            
        try:
            output_folder = self.output_folder_var.get()
            processed_count = self.image_processor.process_images(output_folder, progress_callback)
            
            # Processing completed
            if self.is_processing:
                self.root.after(0, self.processing_completed, processed_count)
            else:
                self.root.after(0, self.processing_cancelled)
                
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Processing Error", str(e))
            self.root.after(0, self.processing_cancelled)
            
    def update_progress(self, current, status):
        """Update progress bar and status."""
        self.progress_bar.config(value=current)
        self.progress_var.set(status)
        
    def processing_completed(self, processed_count):
        """Handle successful completion of processing."""
        self.is_processing = False
        self.process_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set(f"Completed! Processed {processed_count} images")
        self.progress_bar.config(value=processed_count)
        messagebox.showinfo("Processing Complete", 
                           f"Successfully processed {processed_count} images!\n"
                           f"Output saved to: {self.output_folder_var.get()}")
        
    def processing_cancelled(self):
        """Handle cancellation of processing."""
        self.is_processing = False
        self.process_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set("Processing cancelled")
        
    def cancel_processing(self):
        """Cancel the processing operation."""
        self.is_processing = False
        
    def reset_defaults(self):
        """Reset all settings to default values."""
        self.input_folder_var.set(self.default_input_folder)
        self.output_folder_var.set(self.default_output_folder)
        self.crop_x_var.set("1056")
        self.crop_y_var.set("190")
        self.crop_width_var.set("822")
        self.crop_height_var.set("947")
        
        # Reset processor coordinates
        self.image_processor.set_crop_coordinates(1056, 190, 822, 947)
        self.update_crop_preview()
        
    def show_dependency_status(self):
        """Show the status of required dependencies."""
        if self.image_processor.check_dependencies():
            try:
                import PIL
                messagebox.showinfo("Dependencies", f"Pillow is installed:\nVersion {PIL.__version__}")
            except ImportError:
                messagebox.showinfo("Dependencies", "Pillow is available")
        else:
            messagebox.showerror("Dependencies", "Pillow (PIL) is not available.")
            
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About", 
            "Image Crop Tool v1.0\n\n"
            "A GUI interface for batch image cropping.\n"
            "Based on crop.sh script functionality.\n\n"
            "Features:\n"
            "• Batch image processing with Pillow\n"
            "• Interactive crop selection\n"
            "• Image preview with navigation\n"
            "• Mouse-based crop area selection\n"
            "• No external dependencies required"
        )
        
    def show_usage_tips(self):
        """Show usage tips dialog."""
        messagebox.showinfo(
            "Usage Tips",
            "How to use the Image Crop Tool:\n\n"
            "1. Select input folder containing images\n"
            "2. Select output folder for cropped images\n"
            "3. Click 'Load Images' to browse available images\n"
            "4. Use navigation buttons to view different images\n"
            "5. Click and drag on the preview to select crop area\n"
            "6. Fine-tune coordinates in the text fields\n"
            "7. Click 'Process Images' to crop all images\n\n"
            "Tip: The crop area is shown as a red dashed rectangle"
        )


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = CropGUI(root)
    
    # Bind coordinate field changes to update preview and sync to processor
    def on_coordinate_change(*args):
        app.sync_crop_coordinates_to_processor()
        app.update_crop_preview()
        
    for var in [app.crop_x_var, app.crop_y_var, app.crop_width_var, app.crop_height_var]:
        var.trace('w', on_coordinate_change)
    
    root.mainloop()


if __name__ == "__main__":
    main()