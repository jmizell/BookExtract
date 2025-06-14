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
from book_intermediate import BookIntermediate, BookConverter


class EpubGenerator:
    """
    A modular EPUB generation class that handles the creation of EPUB files
    from section array data.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the EPUB generator.
        
        Args:
            logger: Optional logging function that takes (message, level) parameters
        """
        self.logger = logger or self._default_logger
        
    def _default_logger(self, message, level="INFO"):
        """Default logger that prints to console."""
        print(f"[{level}] {message}")
        
    def generate_epub(self, book_data, output_path, base_path=None):
        """
        Generate EPUB from section array data.
        
        Args:
            book_data: List of content sections in the format expected by the renderer
            output_path: Path where the EPUB file should be saved
            base_path: Base path for resolving relative image paths (optional)
            
        Raises:
            ValueError: If required metadata is missing
            Exception: If EPUB generation fails
        """
        # Create a new EPUB book
        book = epub.EpubBook()
        
        # Extract and set metadata
        metadata = self._extract_metadata(book_data)
        self._set_book_metadata(book, metadata)
        
        # Handle cover image
        cover_path = self._resolve_cover_path(metadata['cover_image'], base_path)
        self._set_cover_image(book, cover_path)
        
        # Process content into chapters
        chapters, all_images = self._process_content_to_chapters(book_data, book, base_path)
        
        # Add chapters to the book
        for chapter in chapters:
            self.logger(f"Added chapter {chapter.title}")
            book.add_item(chapter)
            
        # Set up book structure
        self._setup_book_structure(book, chapters)
        
        # Add CSS styling
        self._add_css_styling(book)
        
        # Write the EPUB file
        epub.write_epub(output_path, book, {})
        self.logger(f"EPUB file created: {output_path}")
        
    def _extract_metadata(self, book_data):
        """Extract title, author, and cover from the book data."""
        metadata = {'title': None, 'author': None, 'cover_image': None}
        
        for item in book_data:
            if item['type'] == 'title':
                metadata['title'] = item['content']
            elif item['type'] == 'author':
                metadata['author'] = item['content']
            elif item['type'] == 'cover' and 'image' in item:
                metadata['cover_image'] = item['image']
            if all(metadata.values()):
                break
                
        # Validate required metadata
        if not metadata['title']:
            raise ValueError("ebook is missing section 'title'")
        if not metadata['author']:
            raise ValueError("ebook is missing section 'author'")
        if not metadata['cover_image']:
            raise ValueError("ebook is missing section 'cover_image'")
            
        return metadata
        
    def _set_book_metadata(self, book, metadata):
        """Set the basic metadata for the EPUB book."""
        book_id = str(uuid.uuid4())
        self.logger(f"Set id {book_id}")
        book.set_identifier(book_id)
        self.logger(f"Set title {metadata['title']}")
        book.set_title(metadata['title'])
        self.logger(f"Set language 'en'")
        book.set_language('en')
        self.logger(f"Set author {metadata['author']}")
        book.add_author(metadata['author'])
        
    def _resolve_cover_path(self, cover_image, base_path):
        """Resolve the full path to the cover image."""
        if base_path:
            return os.path.join(base_path, cover_image)
        return cover_image
        
    def _set_cover_image(self, book, cover_path):
        """Set the cover image for the EPUB book."""
        if os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                cover_content = f.read()
            self.logger(f"Set cover {cover_path}")
            book.set_cover("cover.png", cover_content)
        else:
            self.logger(f"Cover image not found: {cover_path}", "WARNING")
            # Create a simple placeholder cover
            placeholder_cover = self._create_placeholder_image()
            book.set_cover("cover.png", placeholder_cover)
            
    def _create_placeholder_image(self):
        """Create a simple placeholder image for missing covers."""
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00[\x8f\x1c\xa6\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
    def _process_content_to_chapters(self, book_data, book, base_path):
        """Process the book data into EPUB chapters."""
        chapters = []
        current_chapter_content = []
        current_chapter_title = "Cover"
        chapter_counter = 0
        division_counter = 0
        image_counter = 1
        all_images = []
        placeholder_cover = self._create_placeholder_image()
        
        for item in book_data:
            if item['type'] == 'chapter_header':
                # Save previous chapter if it has content
                if current_chapter_content:
                    chapter = self._create_chapter(
                        current_chapter_title, chapter_counter, division_counter, current_chapter_content
                    )
                    chapters.append(chapter)
                    chapter_counter += 1
                    current_chapter_content = []
                    
                current_chapter_title = f"Chapter {item['content']}"
                current_chapter_content.append(f"<h1>{item['content']}</h1>")
                division_counter = 1
                
            elif item['type'] == 'title':
                current_chapter_content.append(f"<h1>{item['content']}</h1>")
                
            elif item['type'] == 'author':
                current_chapter_content.append(f"<h2>{item['content']}</h2>")
                
            elif item['type'] in ('cover', 'image') and 'image' in item:
                # Handle images
                img_filename = f"image_{image_counter}.png"
                image_counter += 1
                
                img_path = self._resolve_image_path(item['image'], base_path)
                img_content = self._load_image_content(img_path, placeholder_cover)
                
                # Create image item
                img_item = epub.EpubItem(
                    uid=f"image_{len(all_images) + 1}",
                    file_name=f"images/{img_filename}",
                    media_type="image/png",
                    content=img_content
                )
                book.add_item(img_item)
                all_images.append(img_item)
                
                # Add image reference to chapter content
                self._add_image_to_content(current_chapter_content, img_filename, item.get('caption', ''))
                
            elif item['type'] == 'page_division':
                # Handle page divisions
                if current_chapter_content:
                    chapter = self._create_chapter(
                        current_chapter_title, chapter_counter, division_counter, current_chapter_content
                    )
                    chapters.append(chapter)
                    current_chapter_content = []
                    
                division_counter += 1
                current_chapter_content.append("<hr/>")
                
            else:
                # Handle other content types
                self._add_content_to_chapter(current_chapter_content, item)
                
        # Add the last chapter if there's content
        if current_chapter_content:
            chapter = self._create_chapter(
                current_chapter_title, chapter_counter, division_counter, current_chapter_content
            )
            chapters.append(chapter)
            
        return chapters, all_images
        
    def _resolve_image_path(self, image_name, base_path):
        """Resolve the full path to an image file."""
        if base_path:
            return os.path.join(base_path, image_name)
        return image_name
        
    def _load_image_content(self, img_path, placeholder_content):
        """Load image content from file or return placeholder."""
        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                return f.read()
        else:
            self.logger(f"Image not found: {img_path}, using placeholder", "WARNING")
            return placeholder_content
            
    def _add_image_to_content(self, content_list, img_filename, caption):
        """Add image HTML to the chapter content."""
        if caption:
            content_list.append(
                f'<div class="image-container"><img src="images/{img_filename}" alt="{caption}"/><p class="caption">{caption}</p></div>'
            )
        else:
            content_list.append(
                f'<div class="image-container"><img src="images/{img_filename}" alt="Image"/></div>'
            )
            
    def _add_content_to_chapter(self, content_list, item):
        """Add content item to the chapter based on its type."""
        content_type = item['type']
        content_text = item['content']
        
        if content_type == 'paragraph':
            content_list.append(f"<p>{content_text}</p>")
        elif content_type == 'bold':
            content_list.append(f"<p><strong>{content_text}</strong></p>")
        elif content_type == 'block_indent':
            content_list.append(f"<blockquote>{content_text}</blockquote>")
        elif content_type == 'sub_header':
            content_list.append(f"<h3>{content_text}</h3>")
        elif content_type == 'header':
            content_list.append(f"<h2>{content_text}</h2>")
            
    def _create_chapter(self, title, chapter_counter, division_counter, content_list):
        """Create an EPUB chapter from content."""
        if division_counter > 1:
            chapter_title = f"{title} - {division_counter}"
            file_name = f'chapter_{chapter_counter}.{division_counter}.xhtml'
        else:
            chapter_title = title
            file_name = f'chapter_{chapter_counter}.xhtml'
            
        chapter = epub.EpubHtml(title=chapter_title, file_name=file_name)
        chapter.content = ''.join(content_list)
        return chapter
        
    def _setup_book_structure(self, book, chapters):
        """Set up the book's table of contents and spine."""
        # Define TOC
        book.toc = [(epub.Section('Chapters'), chapters)]
        
        # Add default NCX and Nav files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Create spine
        book.spine = ['nav'] + chapters
        
    def _add_css_styling(self, book):
        """Add CSS styling to the EPUB book."""
        style = '''
        @namespace epub "http://www.idpf.org/2007/ops";
        body {
            font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
            margin: 5%;
            text-align: justify;
        }
        h1, h2, h3 {
            text-align: center;
            margin-bottom: 1em;
        }
        blockquote {
            margin: 1em 2em;
            font-style: italic;
        }
        .image-container {
            text-align: center;
            margin: 1em 0;
        }
        .image-container img {
            max-width: 100%;
            height: auto;
        }
        .caption {
            font-style: italic;
            font-size: 0.9em;
            margin-top: 0.5em;
        }
        '''
        
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)


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
        
        # Preview area
        self.preview_area = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=("Georgia", 11),
            state=tk.DISABLED
        )
        self.preview_area.grid(row=1, column=0, sticky="nsew")
        
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
            
        self.is_rendering = True
        self.render_thread = threading.Thread(target=self._generate_preview)
        self.render_thread.daemon = True
        self.render_thread.start()
        
    def _generate_preview(self):
        """Generate EPUB preview in a separate thread."""
        try:
            self.log_message("Generating EPUB preview...")
            
            if not self.current_intermediate_data:
                self.log_message("No intermediate data to preview", "WARNING")
                return
            
            # Convert intermediate to section array for EPUB generation
            sections = BookConverter.to_section_array(self.current_intermediate_data)
            
            # Create temporary EPUB
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
                self.temp_epub_path = temp_file.name
                
            # Use the modular EPUB generator
            base_path = os.path.dirname(self.current_intermediate_file) if self.current_intermediate_file else self.default_input_folder
            self.epub_generator.generate_epub(sections, self.temp_epub_path, base_path)
            
            # Extract and display content
            preview_text = self._extract_epub_preview(self.temp_epub_path)
            
            # Update preview area
            self.root.after(0, self._update_preview_area, preview_text)
            
        except Exception as e:
            error_msg = f"Preview generation error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.log_message(msg, "ERROR"))
        finally:
            self.is_rendering = False
            
    def _update_preview_area(self, text):
        """Update the preview area with new text."""
        self.preview_area.config(state=tk.NORMAL)
        self.preview_area.delete(1.0, tk.END)
        self.preview_area.insert(1.0, text)
        self.preview_area.config(state=tk.DISABLED)
        self.log_message("Preview updated successfully")
        
    def _extract_epub_preview(self, epub_path):
        """Extract readable text from EPUB for preview."""
        try:
            preview_text = ""
            
            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                # Find content files
                content_files = [f for f in epub_zip.namelist() if f.endswith('.xhtml') and 'chapter' in f]
                content_files.sort()
                
                for content_file in content_files[:5]:  # Limit to first 5 chapters for preview
                    try:
                        content = epub_zip.read(content_file).decode('utf-8')
                        # Simple HTML to text conversion
                        text = self._html_to_text(content)
                        preview_text += f"\n{'='*50}\n{text}\n"
                    except Exception as e:
                        preview_text += f"\n[Error reading {content_file}: {str(e)}]\n"
                        
            return preview_text if preview_text else "No readable content found in EPUB"
            
        except Exception as e:
            return f"Error extracting EPUB preview: {str(e)}"
            
    def _html_to_text(self, html_content):
        """Convert HTML content to plain text for preview."""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities
        text = html.unescape(text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
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