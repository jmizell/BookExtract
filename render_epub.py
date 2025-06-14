#!/usr/bin/env python3
"""
EPUB Renderer Tool - A tkinter interface for EPUB generation from intermediate format.

This application provides a user-friendly interface to load intermediate format files
and generate EPUB files with preview capabilities.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import tempfile
import threading
import webbrowser
from pathlib import Path
import uuid
from ebooklib import epub
import zipfile
import html
from bookextract import BookIntermediate, BookConverter, EpubGenerator, RichTextRenderer


class RenderEpubGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB Renderer Tool")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # State variables
        self.current_intermediate_file = None
        self.current_intermediate_data = None
        self.is_rendering = False
        self.render_thread = None
        self.temp_epub_path = None
        
        # Default values
        self.default_input_folder = str(Path.cwd() / "out")
        self.default_output_folder = str(Path.cwd() / "out")
        
        # Initialize EPUB generator with GUI logger
        self.epub_generator = EpubGenerator(logger=self.log_message)
        
        # Rich text renderer will be initialized after UI setup
        self.rich_text_renderer = None
        
        self.setup_ui()
        self.load_default_intermediate()
        
    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Intermediate...", command=self.open_intermediate, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Export EPUB...", command=self.export_epub, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Clear Log", command=self.clear_log)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Intermediate Format Help", command=self.show_format_help)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_intermediate())
        self.root.bind('<Control-e>', lambda e: self.export_epub())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
    def setup_ui(self):
        """Create and layout the user interface."""
        # Create menu bar
        self.create_menu()
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel - Book Information
        left_frame = ttk.LabelFrame(main_frame, text="Book Information", padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(2, weight=1)
        
        # File info toolbar
        file_toolbar = ttk.Frame(left_frame)
        file_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(file_toolbar, text="Open Intermediate", command=self.open_intermediate).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(file_toolbar, text="Export EPUB", command=self.export_epub).pack(side=tk.LEFT, padx=(0, 2))
        
        # Book metadata display
        metadata_frame = ttk.LabelFrame(left_frame, text="Metadata", padding="5")
        metadata_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        metadata_frame.columnconfigure(1, weight=1)
        
        # Metadata fields
        ttk.Label(metadata_frame, text="Title:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.title_var = tk.StringVar()
        ttk.Label(metadata_frame, textvariable=self.title_var, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w")
        
        ttk.Label(metadata_frame, text="Author:").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.author_var = tk.StringVar()
        ttk.Label(metadata_frame, textvariable=self.author_var).grid(row=1, column=1, sticky="w")
        
        ttk.Label(metadata_frame, text="Language:").grid(row=2, column=0, sticky="w", padx=(0, 5))
        self.language_var = tk.StringVar()
        ttk.Label(metadata_frame, textvariable=self.language_var).grid(row=2, column=1, sticky="w")
        
        ttk.Label(metadata_frame, text="Chapters:").grid(row=3, column=0, sticky="w", padx=(0, 5))
        self.chapters_var = tk.StringVar()
        ttk.Label(metadata_frame, textvariable=self.chapters_var).grid(row=3, column=1, sticky="w")
        
        ttk.Label(metadata_frame, text="Word Count:").grid(row=4, column=0, sticky="w", padx=(0, 5))
        self.word_count_var = tk.StringVar()
        ttk.Label(metadata_frame, textvariable=self.word_count_var).grid(row=4, column=1, sticky="w")
        
        # Chapter list
        chapters_frame = ttk.LabelFrame(left_frame, text="Chapters", padding="5")
        chapters_frame.grid(row=2, column=0, sticky="nsew")
        chapters_frame.columnconfigure(0, weight=1)
        chapters_frame.rowconfigure(0, weight=1)
        
        # Chapter listbox with scrollbar
        list_frame = ttk.Frame(chapters_frame)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.chapters_listbox = tk.Listbox(list_frame, font=("Arial", 9))
        self.chapters_listbox.grid(row=0, column=0, sticky="nsew")
        
        chapters_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.chapters_listbox.yview)
        chapters_scrollbar.grid(row=0, column=1, sticky="ns")
        self.chapters_listbox.configure(yscrollcommand=chapters_scrollbar.set)
        
        # Right panel - EPUB Preview
        right_frame = ttk.LabelFrame(main_frame, text="EPUB Preview", padding="5")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Preview area with rich text support
        self.preview_area = tk.Text(
            right_frame,
            wrap=tk.WORD,
            font=("Georgia", 11),
            state=tk.DISABLED,
            bg="white",
            fg="black"
        )
        self.preview_area.grid(row=1, column=0, sticky="nsew")
        
        # Add scrollbar to preview area
        preview_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.preview_area.yview)
        preview_scrollbar.grid(row=1, column=1, sticky="ns")
        self.preview_area.configure(yscrollcommand=preview_scrollbar.set)
        right_frame.columnconfigure(1, weight=0)
        
        # Initialize rich text renderer
        self.rich_text_renderer = RichTextRenderer(
            self.preview_area, 
            self.default_input_folder, 
            self.log_message
        )
        
        # Bottom panel - Log console
        log_frame = ttk.LabelFrame(main_frame, text="Log Console", padding="5")
        log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        log_frame.columnconfigure(0, weight=1)
        
        # Log toolbar
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(log_toolbar, text="Clear", command=self.clear_log).pack(side=tk.LEFT)
        
        # Log text area
        self.log_console = scrolledtext.ScrolledText(
            log_frame,
            height=6,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.log_console.grid(row=1, column=0, sticky="ew")
        
        # Configure row weights for log section
        main_frame.rowconfigure(1, weight=0)
        
    def log_message(self, message, level="INFO"):
        """Add a message to the log console."""
        self.log_console.config(state=tk.NORMAL)
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_console.insert(tk.END, f"[{timestamp}] {level}: {message}\n")
        self.log_console.see(tk.END)
        self.log_console.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log console."""
        self.log_console.config(state=tk.NORMAL)
        self.log_console.delete(1.0, tk.END)
        self.log_console.config(state=tk.DISABLED)
        
    def open_intermediate(self):
        """Open an intermediate representation file."""
        file_path = filedialog.askopenfilename(
            title="Open Intermediate File",
            initialdir=self.default_input_folder,
            filetypes=[
                ("Intermediate files", "*.json"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Load intermediate representation
                intermediate = BookIntermediate.load_from_file(file_path)
                
                self.current_intermediate_file = file_path
                self.current_intermediate_data = intermediate
                self.update_metadata_display(intermediate)
                self.update_chapters_list(intermediate)
                self.log_message(f"Opened intermediate file: {file_path}")
                self.log_message(f"Loaded {intermediate.get_chapter_count()} chapters, {intermediate.get_total_word_count()} words")
                self.refresh_preview()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open intermediate file:\n{str(e)}")
                self.log_message(f"Error opening intermediate file: {str(e)}", "ERROR")
    
    def update_metadata_display(self, intermediate):
        """Update the metadata display with book information."""
        self.title_var.set(intermediate.metadata.title or "Unknown Title")
        self.author_var.set(intermediate.metadata.author or "Unknown Author")
        self.language_var.set(intermediate.metadata.language or "Unknown")
        self.chapters_var.set(str(intermediate.get_chapter_count()))
        self.word_count_var.set(f"{intermediate.get_total_word_count():,}")
        
    def update_chapters_list(self, intermediate):
        """Update the chapters list with chapter information."""
        self.chapters_listbox.delete(0, tk.END)
        
        for chapter in intermediate.chapters:
            word_count = chapter.get_word_count()
            chapter_text = f"Chapter {chapter.number}: {chapter.title} ({word_count:,} words)"
            self.chapters_listbox.insert(tk.END, chapter_text)
            
    def refresh_preview(self):
        """Refresh the EPUB preview."""
        if not self.current_intermediate_data:
            self.log_message("No intermediate data loaded", "WARNING")
            return
            
        if self.is_rendering:
            return
        
        # Clear image cache to free memory and reload images
        if self.rich_text_renderer:
            self.rich_text_renderer.clear_image_cache()
            
        self.is_rendering = True
        self.render_thread = threading.Thread(target=self._generate_preview)
        self.render_thread.daemon = True
        self.render_thread.start()
        
    def _generate_preview(self):
        """Generate rich text preview in a separate thread."""
        try:
            self.log_message("Generating rich text preview...")
            
            if not self.current_intermediate_data:
                self.log_message("No intermediate data to preview", "WARNING")
                return
            
            # Update base path for image resolution
            if self.rich_text_renderer:
                if self.current_intermediate_file:
                    base_path = os.path.dirname(self.current_intermediate_file)
                else:
                    base_path = self.default_input_folder
                self.rich_text_renderer.set_base_path(base_path)
                
                # Render using the shared renderer
                self.root.after(0, self._render_preview, self.current_intermediate_data)
            
        except Exception as e:
            error_msg = f"Preview generation error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.log_message(msg, "ERROR"))
        finally:
            self.is_rendering = False
            
    def _render_preview(self, intermediate_data):
        """Render the preview using the RichTextRenderer."""
        try:
            if self.rich_text_renderer:
                self.rich_text_renderer.render_intermediate_data(intermediate_data)
        except Exception as e:
            self.log_message(f"Rendering error: {str(e)}", "ERROR")

        
    def export_epub(self):
        """Export the current intermediate data as an EPUB file."""
        if not self.current_intermediate_data:
            messagebox.showwarning("Warning", "No intermediate data loaded")
            return
            
        try:
            intermediate = self.current_intermediate_data
            
            # Get default filename from metadata
            default_filename = f"{intermediate.metadata.title} - {intermediate.metadata.author}.epub"
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                title="Export EPUB",
                initialdir=self.default_output_folder,
                initialfile=default_filename,
                defaultextension=".epub",
                filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
            )
            
            if file_path:
                self.log_message(f"Exporting EPUB to: {file_path}")
                
                # Convert intermediate to section array for EPUB generation
                sections = BookConverter.to_section_array(intermediate)
                
                # Use the modular EPUB generator
                base_path = os.path.dirname(self.current_intermediate_file) if self.current_intermediate_file else self.default_input_folder
                self.epub_generator.generate_epub(sections, file_path, base_path)
                
                messagebox.showinfo("Success", f"EPUB exported successfully to:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export EPUB:\n{str(e)}")
            self.log_message(f"Export error: {str(e)}", "ERROR")
            
    def load_default_intermediate(self):
        """Load default intermediate file if available."""
        default_paths = [
            os.path.join(self.default_input_folder, "book_intermediate.json"),
            os.path.join(self.default_input_folder, "book.intermediate.json")
        ]
        
        for default_path in default_paths:
            if os.path.exists(default_path):
                try:
                    intermediate = BookIntermediate.load_from_file(default_path)
                    
                    self.current_intermediate_file = default_path
                    self.current_intermediate_data = intermediate
                    self.update_metadata_display(intermediate)
                    self.update_chapters_list(intermediate)
                    self.log_message(f"Loaded default intermediate: {default_path}")
                    self.refresh_preview()
                    return
                    
                except Exception as e:
                    self.log_message(f"Could not load default intermediate: {str(e)}", "WARNING")
                    
        self.log_message("No default intermediate file found")
        
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About EPUB Renderer Tool",
            "EPUB Renderer Tool v1.0\n\n"
            "A specialized tool for generating EPUB files from intermediate format.\n\n"
            "Features:\n"
            "• Load intermediate format files\n"
            "• Generate EPUB files\n"
            "• EPUB preview\n"
            "• Book metadata display\n"
            "• Chapter organization view"
        )
        
    def show_format_help(self):
        """Show intermediate format help."""
        help_text = """Intermediate Format Help

The EPUB Renderer Tool works with BookExtract intermediate format files.

Supported File Types:
• .json files containing intermediate format data
• Files created by epub_extractor.py with --intermediate flag
• Files saved from render_book.py as intermediate format

File Structure:
The intermediate format contains:
• Book metadata (title, author, language, etc.)
• Organized chapters with content sections
• Word count and chapter statistics

Loading Files:
• Use File → Open Intermediate... to load files
• The tool will display book metadata and chapter list
• Preview shows EPUB content extracted from generated file

Generating EPUB:
• Use File → Export EPUB... to create EPUB files
• Images are loaded from the same directory as the intermediate file
• Missing images are replaced with placeholders

Requirements:
• Intermediate files must contain title, author, and cover sections
• Image files should be in the same directory as the intermediate file
• Cover image is required for EPUB generation

For more information about the intermediate format, see:
INTERMEDIATE_FORMAT.md
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Intermediate Format Help")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=("Consolas", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)


def main():
    """Main function to run the application."""
    # Fix datetime import issue
    import datetime
    tk.datetime = datetime
    
    root = tk.Tk()
    app = RenderEpubGUI(root)
    
    # Handle window closing
    def on_closing():
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()


if __name__ == "__main__":
    main()