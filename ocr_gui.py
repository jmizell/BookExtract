#!/usr/bin/env python3
"""
GUI version of ocr.sh and ocr.py - A tkinter interface for OCR processing.

This application provides a user-friendly interface to perform OCR on images
using tesseract for basic OCR, followed by vision LLM cleanup for structured output.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import time
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import glob
from bookextract import OCRProcessor


class OCRGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Processing Tool")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # State variables
        self.is_processing = False
        self.process_thread = None
        self.current_step = ""
        self.total_files = 0
        self.processed_files = 0
        
        # Default values
        self.default_input_folder = str(Path.cwd() / "out")
        self.default_output_folder = str(Path.cwd() / "out")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize OCR processor
        self.ocr_processor = OCRProcessor()
        self.ocr_processor.set_callbacks(
            progress_callback=self.update_progress_from_processor,
            log_callback=self.log_message_from_processor
        )
        
        self.setup_ui()
        
    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load .env File", command=self.load_env_file)
        file_menu.add_command(label="Reset to Defaults", command=self.reset_defaults)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test API Connection", command=self.test_api_connection)
        tools_menu.add_command(label="Check Dependencies", command=self.show_dependency_status)
        tools_menu.add_command(label="Preview Results", command=self.preview_results)
        
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
        
        # Main frame with scrollable content
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="OCR Processing Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input/Output directories section
        dirs_frame = ttk.LabelFrame(main_frame, text="Directories", padding="10")
        dirs_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        dirs_frame.columnconfigure(1, weight=1)
        
        # Input folder
        ttk.Label(dirs_frame, text="Input folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_folder_var = tk.StringVar(value=self.default_input_folder)
        input_entry = ttk.Entry(dirs_frame, textvariable=self.input_folder_var)
        input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        input_browse_button = ttk.Button(dirs_frame, text="Browse", 
                                        command=self.browse_input_folder)
        input_browse_button.grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Output folder
        ttk.Label(dirs_frame, text="Output folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_folder_var = tk.StringVar(value=self.default_output_folder)
        output_entry = ttk.Entry(dirs_frame, textvariable=self.output_folder_var)
        output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        output_browse_button = ttk.Button(dirs_frame, text="Browse", 
                                         command=self.browse_output_folder)
        output_browse_button.grid(row=1, column=2, padx=(5, 0), pady=5)
        
        # OCR Settings section
        ocr_frame = ttk.LabelFrame(main_frame, text="OCR Settings", padding="10")
        ocr_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        ocr_frame.columnconfigure(1, weight=1)
        
        # Processing mode
        ttk.Label(ocr_frame, text="Processing mode:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.processing_mode_var = tk.StringVar(value="full")
        mode_frame = ttk.Frame(ocr_frame)
        mode_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        ttk.Radiobutton(mode_frame, text="Basic OCR only", variable=self.processing_mode_var, 
                       value="basic").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Full pipeline (OCR + LLM + Merge)", 
                       variable=self.processing_mode_var, value="full").pack(side=tk.LEFT)
        
        # Include merge step option
        self.include_merge_var = tk.BooleanVar(value=True)
        merge_check = ttk.Checkbutton(ocr_frame, text="Include merge step (fix content split across pages)", 
                                     variable=self.include_merge_var)
        merge_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Max workers for LLM processing
        ttk.Label(ocr_frame, text="Max workers:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.max_workers_var = tk.StringVar(value="15")
        workers_spinbox = ttk.Spinbox(ocr_frame, from_=1, to=50, width=10, 
                                     textvariable=self.max_workers_var)
        workers_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # API Configuration section
        api_frame = ttk.LabelFrame(main_frame, text="API Configuration (for LLM cleanup and merge)", padding="10")
        api_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        api_frame.columnconfigure(1, weight=1)
        
        # API URL
        ttk.Label(api_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_url_var = tk.StringVar(value=os.getenv("API_URL", ""))
        api_url_entry = ttk.Entry(api_frame, textvariable=self.api_url_var)
        api_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # API Token
        ttk.Label(api_frame, text="API Token:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_token_var = tk.StringVar(value=os.getenv("API_TOKEN", ""))
        api_token_entry = ttk.Entry(api_frame, textvariable=self.api_token_var, show="*")
        api_token_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Model
        ttk.Label(api_frame, text="Model:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=os.getenv("MODEL", ""))
        model_entry = ttk.Entry(api_frame, textvariable=self.model_var)
        model_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to process")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Processing", 
                                      command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", 
                                       command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_api_button = ttk.Button(button_frame, text="Test API", 
                                         command=self.test_api_connection)
        self.test_api_button.pack(side=tk.LEFT)
        
        # Status text area
        status_frame = ttk.LabelFrame(main_frame, text="Status Log", padding="5")
        status_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        self.status_text = tk.Text(status_frame, height=12, wrap=tk.WORD)
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Pack the canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configure canvas scrolling with mouse wheel
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Initial status message
        self.log_message("Application started. Configure settings and click 'Start Processing' to begin.")
        
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
            title="Select output folder for OCR results",
            initialdir=self.output_folder_var.get()
        )
        if directory:
            self.output_folder_var.set(directory)
            
    def load_env_file(self):
        """Load environment variables from a .env file."""
        file_path = filedialog.askopenfilename(
            title="Select .env file",
            filetypes=[("Environment files", "*.env"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Load the new .env file
                load_dotenv(file_path, override=True)
                
                # Update the GUI fields
                self.api_url_var.set(os.getenv("API_URL", ""))
                self.api_token_var.set(os.getenv("API_TOKEN", ""))
                self.model_var.set(os.getenv("MODEL", ""))
                
                self.log_message(f"Loaded environment variables from {file_path}")
                messagebox.showinfo("Success", "Environment variables loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load .env file: {e}")
                
    def log_message(self, message):
        """Add a message to the status log."""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def log_message_from_processor(self, message):
        """Callback method for OCR processor to log messages."""
        self.root.after(0, self.log_message, message)
        
    def update_progress_from_processor(self, current, status):
        """Callback method for OCR processor to update progress."""
        self.root.after(0, self.update_progress, current, status)
        
    def validate_inputs(self):
        """Validate user inputs before starting processing."""
        input_folder = Path(self.input_folder_var.get())
        if not input_folder.exists():
            messagebox.showerror("Invalid Input", f"Input folder does not exist: {input_folder}")
            return False
            
        output_folder = self.output_folder_var.get().strip()
        if not output_folder:
            messagebox.showerror("Invalid Input", "Please specify an output folder")
            return False
            
        # Check for images in input folder
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(str(input_folder / ext)))
            image_files.extend(glob.glob(str(input_folder / ext.upper())))
            
        if not image_files:
            messagebox.showerror("No Images", f"No image files found in {input_folder}")
            return False
            
        # Validate API settings if full pipeline is selected
        if self.processing_mode_var.get() == "full":
            if not self.api_url_var.get().strip():
                messagebox.showerror("Invalid Input", "API URL is required for full pipeline processing")
                return False
            if not self.api_token_var.get().strip():
                messagebox.showerror("Invalid Input", "API Token is required for full pipeline processing")
                return False
            if not self.model_var.get().strip():
                messagebox.showerror("Invalid Input", "Model is required for full pipeline processing")
                return False
                
        try:
            max_workers = int(self.max_workers_var.get())
            if max_workers <= 0:
                raise ValueError("Max workers must be positive")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of max workers (positive integer)")
            return False
            
        return True
        
    def check_dependencies(self):
        """Check if required system tools are available."""
        required_tools = ['tesseract']
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
                "Please install tesseract using:\nsudo apt-get install tesseract-ocr"
            )
            return False
            
        return True
        
    def test_api_connection(self):
        """Test the API connection."""
        if not self.api_url_var.get().strip() or not self.api_token_var.get().strip():
            messagebox.showwarning("Missing Configuration", "Please configure API URL and Token first")
            return
            
        self.log_message("Testing API connection...")
        
        # Update processor with current settings
        self.ocr_processor.api_url = self.api_url_var.get()
        self.ocr_processor.api_token = self.api_token_var.get()
        self.ocr_processor.model = self.model_var.get()
        
        success, message = self.ocr_processor.test_api_connection()
        
        self.log_message(message)
        if success:
            messagebox.showinfo("Success", "API connection test successful!")
        else:
            messagebox.showerror("API Error", message)
            
    def start_processing(self):
        """Start the OCR processing."""
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
        self.processed_files = 0
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # Count total files to process
        input_folder = Path(self.input_folder_var.get())
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(str(input_folder / ext)))
            image_files.extend(glob.glob(str(input_folder / ext.upper())))
        
        self.total_files = len(image_files)
        self.progress_bar.config(maximum=self.total_files, value=0)
        
        # Start processing in separate thread
        self.process_thread = threading.Thread(target=self.processing_worker, daemon=True)
        self.process_thread.start()
        
        if self.processing_mode_var.get() == "basic":
            mode = "Basic OCR"
        else:
            mode = "Full pipeline (OCR + LLM"
            if self.include_merge_var.get():
                mode += " + Merge"
            mode += ")"
        self.log_message(f"Starting {mode} processing of {self.total_files} images...")
        
    def processing_worker(self):
        """Worker thread for the processing."""
        try:
            input_folder = Path(self.input_folder_var.get())
            output_folder = Path(self.output_folder_var.get())
            
            # Update processor with current settings
            self.ocr_processor.api_url = self.api_url_var.get()
            self.ocr_processor.api_token = self.api_token_var.get()
            self.ocr_processor.model = self.model_var.get()
            self.ocr_processor.max_workers = int(self.max_workers_var.get())
            self.ocr_processor.is_cancelled = False
            
            # Step 1: Basic OCR with tesseract
            self.root.after(0, self.update_progress, 0, "Running basic OCR...")
            
            if not self.ocr_processor.run_basic_ocr(input_folder, output_folder, self.total_files):
                self.root.after(0, self.processing_failed, "Basic OCR failed")
                return
                
            # Step 2: LLM cleanup (if full pipeline selected)
            if self.processing_mode_var.get() == "full":
                progress_offset = self.total_files // 3 if self.include_merge_var.get() else self.total_files // 2
                self.root.after(0, self.update_progress, progress_offset, "Running LLM cleanup...")
                
                if not self.ocr_processor.run_llm_cleanup(output_folder, self.total_files):
                    self.root.after(0, self.processing_failed, "LLM cleanup failed")
                    return
                    
                # Step 3: Merge step (if enabled)
                if self.include_merge_var.get():
                    progress_offset = (self.total_files * 2) // 3
                    self.root.after(0, self.update_progress, progress_offset, "Merging content across pages...")
                    
                    if not self.ocr_processor.run_merge_step(output_folder):
                        self.root.after(0, self.processing_failed, "Merge step failed")
                        return
                    
            # Processing completed
            self.root.after(0, self.processing_completed)
            
        except Exception as e:
            self.root.after(0, self.processing_failed, f"Unexpected error: {e}")
            
    def update_progress(self, current, status):
        """Update progress bar and status."""
        self.progress_bar.config(value=current)
        self.progress_var.set(status)
        
    def processing_completed(self):
        """Handle successful completion of processing."""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        
        if self.processing_mode_var.get() == "basic":
            mode = "Basic OCR"
        else:
            mode = "Full pipeline"
            if self.include_merge_var.get():
                mode += " with merge"
                
        self.progress_var.set(f"Completed! Processed {self.total_files} files")
        self.progress_bar.config(value=self.total_files)
        self.log_message(f"{mode} processing completed successfully! Results saved to {self.output_folder_var.get()}")
        
        if self.processing_mode_var.get() == "full" and self.include_merge_var.get():
            self.log_message("Final merged content available in book.json")
        
        messagebox.showinfo("Processing Complete", f"{mode} processing completed successfully!")
        
    def processing_failed(self, error_message):
        """Handle processing failure."""
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set("Processing failed")
        self.log_message(f"Processing failed: {error_message}")
        
        messagebox.showerror("Processing Failed", f"Processing failed: {error_message}")
        
    def cancel_processing(self):
        """Cancel the current processing."""
        self.is_processing = False
        self.ocr_processor.cancel()
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set("Processing cancelled")
        self.log_message("Processing cancelled by user")
        
    def preview_results(self):
        """Preview the OCR results."""
        output_folder = Path(self.output_folder_var.get())
        
        # Find result files
        txt_files = list(output_folder.glob("*.txt"))
        json_files = list(output_folder.glob("*.json"))
        book_json = output_folder / "book.json"
        
        if not txt_files and not json_files:
            messagebox.showinfo("No Results", "No OCR results found in the output folder")
            return
            
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("OCR Results Preview")
        preview_window.geometry("800x600")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(preview_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text results tab
        if txt_files:
            txt_frame = ttk.Frame(notebook)
            notebook.add(txt_frame, text=f"Text Results ({len(txt_files)} files)")
            
            txt_listbox = tk.Listbox(txt_frame)
            txt_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
            
            txt_text = tk.Text(txt_frame, wrap=tk.WORD)
            txt_scrollbar = ttk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=txt_text.yview)
            txt_text.configure(yscrollcommand=txt_scrollbar.set)
            txt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            txt_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Populate text files list
            for txt_file in sorted(txt_files):
                txt_listbox.insert(tk.END, txt_file.name)
                
            def show_txt_file(event):
                selection = txt_listbox.curselection()
                if selection:
                    file_path = txt_files[selection[0]]
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        txt_text.delete(1.0, tk.END)
                        txt_text.insert(1.0, content)
                    except Exception as e:
                        txt_text.delete(1.0, tk.END)
                        txt_text.insert(1.0, f"Error reading file: {e}")
                        
            txt_listbox.bind('<<ListboxSelect>>', show_txt_file)
            
        # JSON results tab
        if json_files:
            json_frame = ttk.Frame(notebook)
            notebook.add(json_frame, text=f"JSON Results ({len(json_files)} files)")
            
            json_listbox = tk.Listbox(json_frame)
            json_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
            
            json_text = tk.Text(json_frame, wrap=tk.WORD)
            json_scrollbar = ttk.Scrollbar(json_frame, orient=tk.VERTICAL, command=json_text.yview)
            json_text.configure(yscrollcommand=json_scrollbar.set)
            json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            json_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Populate JSON files list
            for json_file in sorted(json_files):
                json_listbox.insert(tk.END, json_file.name)
                
            def show_json_file(event):
                selection = json_listbox.curselection()
                if selection:
                    file_path = json_files[selection[0]]
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        json_text.delete(1.0, tk.END)
                        json_text.insert(1.0, json.dumps(content, indent=2, ensure_ascii=False))
                    except Exception as e:
                        json_text.delete(1.0, tk.END)
                        json_text.insert(1.0, f"Error reading file: {e}")
                        
            json_listbox.bind('<<ListboxSelect>>', show_json_file)
            
        # Merged book tab (if book.json exists)
        if book_json.exists():
            book_frame = ttk.Frame(notebook)
            notebook.add(book_frame, text="Merged Book (book.json)")
            
            book_text = tk.Text(book_frame, wrap=tk.WORD)
            book_scrollbar = ttk.Scrollbar(book_frame, orient=tk.VERTICAL, command=book_text.yview)
            book_text.configure(yscrollcommand=book_scrollbar.set)
            book_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            book_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Load and display book.json
            try:
                with open(book_json, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                book_text.insert(1.0, json.dumps(content, indent=2, ensure_ascii=False))
            except Exception as e:
                book_text.insert(1.0, f"Error reading book.json: {e}")
            
    def reset_defaults(self):
        """Reset all settings to default values."""
        self.input_folder_var.set(self.default_input_folder)
        self.output_folder_var.set(self.default_output_folder)
        self.processing_mode_var.set("full")
        self.include_merge_var.set(True)
        self.max_workers_var.set("15")
        self.api_url_var.set("")
        self.api_token_var.set("")
        self.model_var.set("")
        self.log_message("Settings reset to defaults")
        
    def show_dependency_status(self):
        """Show the status of required dependencies."""
        status_lines = []
        
        # Check tesseract
        try:
            result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                status_lines.append(f"✓ Tesseract: {version_line}")
            else:
                status_lines.append("✗ Tesseract: Not working properly")
        except FileNotFoundError:
            status_lines.append("✗ Tesseract: Not installed")
            
        # Check Python packages
        try:
            import requests
            status_lines.append("✓ requests: Available")
        except ImportError:
            status_lines.append("✗ requests: Not installed")
            
        try:
            from dotenv import load_dotenv
            status_lines.append("✓ python-dotenv: Available")
        except ImportError:
            status_lines.append("✗ python-dotenv: Not installed")
            
        messagebox.showinfo("Dependency Status", "\n".join(status_lines))
        
    def show_about(self):
        """Show about dialog."""
        about_text = """OCR Processing Tool

A GUI application for processing book images with OCR.

Features:
• Basic OCR using Tesseract
• LLM-powered OCR cleanup and structuring
• Batch processing with progress tracking
• Configurable API settings
• Results preview

This tool combines the functionality of ocr.sh and ocr.py
into a user-friendly graphical interface.
"""
        messagebox.showinfo("About", about_text)
        
    def show_usage_tips(self):
        """Show usage tips dialog."""
        tips_text = """Usage Tips:

1. Input Folder: Select the folder containing your cropped book page images

2. Processing Modes:
   • Basic OCR: Only runs Tesseract OCR to extract text
   • Full Pipeline: Runs OCR + LLM cleanup + merge for structured JSON output

3. API Configuration:
   • Required for full pipeline processing
   • Load from .env file or enter manually
   • Test connection before processing

4. Merge Step:
   • Fixes content split across page breaks
   • Uses smart heuristics to minimize API calls
   • Can be disabled if not needed

5. Results:
   • Text files (.txt) contain raw OCR output
   • JSON files (.json) contain structured, cleaned content per page
   • book.json contains final merged content across all pages
   • Use Preview Results to view processed files

6. Performance:
   • Adjust Max Workers for LLM processing based on your API limits
   • Processing time depends on image count and API response time
"""
        messagebox.showinfo("Usage Tips", tips_text)


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = OCRGUI(root)
    
    # Center the window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()