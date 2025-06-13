#!/usr/bin/env python3
"""
GUI version of render.py - A tkinter interface for EPUB generation and preview.

This application provides a user-friendly interface to edit book JSON data,
generate EPUB files, and preview the rendered content.
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


class RenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB Render Tool")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # State variables
        self.current_json_file = None
        self.current_json_data = None
        self.is_rendering = False
        self.render_thread = None
        self.temp_epub_path = None
        
        # Default values
        self.default_input_folder = str(Path.cwd() / "out")
        self.default_output_folder = str(Path.cwd() / "out")
        
        self.setup_ui()
        self.load_default_json()
        
    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_json, accelerator="Ctrl+N")
        file_menu.add_command(label="Open JSON...", command=self.open_json, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save JSON", command=self.save_json, accelerator="Ctrl+S")
        file_menu.add_command(label="Save JSON As...", command=self.save_json_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export EPUB...", command=self.export_epub, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Format JSON", command=self.format_json, accelerator="Ctrl+F")
        edit_menu.add_command(label="Validate JSON", command=self.validate_json, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear Log", command=self.clear_log)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Preview", command=self.refresh_preview, accelerator="F5")
        view_menu.add_command(label="Open EPUB in Browser", command=self.open_epub_in_browser, accelerator="Ctrl+B")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="JSON Format Help", command=self.show_json_help)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_json())
        self.root.bind('<Control-o>', lambda e: self.open_json())
        self.root.bind('<Control-s>', lambda e: self.save_json())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_json_as())
        self.root.bind('<Control-e>', lambda e: self.export_epub())
        self.root.bind('<Control-f>', lambda e: self.format_json())
        self.root.bind('<Control-v>', lambda e: self.validate_json())
        self.root.bind('<Control-b>', lambda e: self.open_epub_in_browser())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F5>', lambda e: self.refresh_preview())
        
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
        
        # Left panel - JSON Editor
        left_frame = ttk.LabelFrame(main_frame, text="JSON Editor", padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # JSON editor toolbar
        json_toolbar = ttk.Frame(left_frame)
        json_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(json_toolbar, text="Open", command=self.open_json).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(json_toolbar, text="Save", command=self.save_json).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(json_toolbar, text="Format", command=self.format_json).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(json_toolbar, text="Validate", command=self.validate_json).pack(side=tk.LEFT, padx=(0, 2))
        
        # JSON text editor
        self.json_editor = scrolledtext.ScrolledText(
            left_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            undo=True,
            maxundo=50
        )
        self.json_editor.grid(row=1, column=0, sticky="nsew")
        
        # Right panel - Preview
        right_frame = ttk.LabelFrame(main_frame, text="EPUB Preview", padding="5")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Preview toolbar
        preview_toolbar = ttk.Frame(right_frame)
        preview_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(preview_toolbar, text="Refresh", command=self.refresh_preview).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(preview_toolbar, text="Export EPUB", command=self.export_epub).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(preview_toolbar, text="Open in Browser", command=self.open_epub_in_browser).pack(side=tk.LEFT, padx=(0, 2))
        
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
            height=8,
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
        timestamp = tk.datetime.datetime.now().strftime("%H:%M:%S")
        self.log_console.insert(tk.END, f"[{timestamp}] {level}: {message}\n")
        self.log_console.see(tk.END)
        self.log_console.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log console."""
        self.log_console.config(state=tk.NORMAL)
        self.log_console.delete(1.0, tk.END)
        self.log_console.config(state=tk.DISABLED)
        
    def new_json(self):
        """Create a new JSON document."""
        if self.check_unsaved_changes():
            return
            
        default_json = [
            {
                "type": "title",
                "content": "Sample Book Title"
            },
            {
                "type": "author",
                "content": "Sample Author"
            },
            {
                "type": "cover",
                "image": "cover.png"
            },
            {
                "type": "chapter_header",
                "content": "1"
            },
            {
                "type": "paragraph",
                "content": "This is a sample paragraph in the first chapter."
            }
        ]
        
        self.json_editor.delete(1.0, tk.END)
        self.json_editor.insert(1.0, json.dumps(default_json, indent=2))
        self.current_json_file = None
        self.current_json_data = default_json
        self.log_message("Created new JSON document")
        self.refresh_preview()
        
    def open_json(self):
        """Open a JSON file."""
        if self.check_unsaved_changes():
            return
            
        file_path = filedialog.askopenfilename(
            title="Open JSON File",
            initialdir=self.default_input_folder,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.json_editor.delete(1.0, tk.END)
                self.json_editor.insert(1.0, json.dumps(data, indent=2))
                self.current_json_file = file_path
                self.current_json_data = data
                self.log_message(f"Opened JSON file: {file_path}")
                self.refresh_preview()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open JSON file:\n{str(e)}")
                self.log_message(f"Error opening JSON file: {str(e)}", "ERROR")
                
    def save_json(self):
        """Save the current JSON file."""
        if self.current_json_file:
            self._save_json_to_file(self.current_json_file)
        else:
            self.save_json_as()
            
    def save_json_as(self):
        """Save the JSON file with a new name."""
        file_path = filedialog.asksaveasfilename(
            title="Save JSON File",
            initialdir=self.default_output_folder,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self._save_json_to_file(file_path)
            self.current_json_file = file_path
            
    def _save_json_to_file(self, file_path):
        """Save JSON content to a file."""
        try:
            # Validate JSON first
            json_text = self.json_editor.get(1.0, tk.END).strip()
            data = json.loads(json_text)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.current_json_data = data
            self.log_message(f"Saved JSON file: {file_path}")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format:\n{str(e)}")
            self.log_message(f"JSON validation error: {str(e)}", "ERROR")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save JSON file:\n{str(e)}")
            self.log_message(f"Error saving JSON file: {str(e)}", "ERROR")
            
    def format_json(self):
        """Format the JSON in the editor."""
        try:
            json_text = self.json_editor.get(1.0, tk.END).strip()
            data = json.loads(json_text)
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            
            self.json_editor.delete(1.0, tk.END)
            self.json_editor.insert(1.0, formatted_json)
            self.log_message("JSON formatted successfully")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format:\n{str(e)}")
            self.log_message(f"JSON formatting error: {str(e)}", "ERROR")
            
    def validate_json(self):
        """Validate the JSON in the editor and insert stubs for missing required sections."""
        try:
            json_text = self.json_editor.get(1.0, tk.END).strip()
            data = json.loads(json_text)
            
            # Basic validation for required fields
            has_title = any(item.get('type') == 'title' for item in data)
            has_author = any(item.get('type') == 'author' for item in data)
            has_cover = any(item.get('type') == 'cover' for item in data)
            
            missing_sections = []
            stubs_added = []
            
            # Check for missing sections and prepare stubs
            if not has_title:
                missing_sections.append("title")
            if not has_author:
                missing_sections.append("author")
            if not has_cover:
                missing_sections.append("cover")
                
            if missing_sections:
                # Ask user if they want to add stubs
                response = messagebox.askyesno(
                    "Missing Required Sections",
                    f"The following required sections are missing:\n" + 
                    "\n".join(f"• {section}" for section in missing_sections) +
                    "\n\nWould you like to automatically add stub entries for these sections?"
                )
                
                if response:
                    # Create a new data list with stubs inserted at the beginning
                    new_data = []
                    
                    # Add missing stubs at the beginning
                    if not has_title:
                        new_data.append({
                            "type": "title",
                            "content": "Your Book Title Here"
                        })
                        stubs_added.append("title")
                        
                    if not has_author:
                        new_data.append({
                            "type": "author", 
                            "content": "Your Name Here"
                        })
                        stubs_added.append("author")
                        
                    if not has_cover:
                        new_data.append({
                            "type": "cover",
                            "image": "cover.png"
                        })
                        stubs_added.append("cover")
                    
                    # Add existing data
                    new_data.extend(data)
                    
                    # Update the editor with the new JSON
                    formatted_json = json.dumps(new_data, indent=2, ensure_ascii=False)
                    self.json_editor.delete(1.0, tk.END)
                    self.json_editor.insert(1.0, formatted_json)
                    
                    # Log the changes
                    self.log_message(f"Added stub entries for: {', '.join(stubs_added)}")
                    messagebox.showinfo(
                        "Stubs Added", 
                        f"Added stub entries for: {', '.join(stubs_added)}\n\n" +
                        "Please update the placeholder content with your actual information."
                    )
                else:
                    # User declined to add stubs
                    self.log_message(f"JSON validation issues: {', '.join(missing_sections)}", "WARNING")
                    messagebox.showwarning(
                        "Validation Issues", 
                        "JSON validation issues:\n" + 
                        "\n".join(f"• Missing '{section}' entry" for section in missing_sections)
                    )
            else:
                # All required sections present
                messagebox.showinfo("Validation", "JSON is valid! All required sections are present.")
                self.log_message("JSON validation successful - all required sections present")
                
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format:\n{str(e)}")
            self.log_message(f"JSON validation error: {str(e)}", "ERROR")
            
    def refresh_preview(self):
        """Refresh the EPUB preview."""
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
            
            # Parse JSON
            json_text = self.json_editor.get(1.0, tk.END).strip()
            if not json_text:
                self.log_message("No JSON content to preview", "WARNING")
                return
                
            data = json.loads(json_text)
            
            # Create temporary EPUB
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
                self.temp_epub_path = temp_file.name
                
            self._generate_epub_from_data(data, self.temp_epub_path)
            
            # Extract and display content
            preview_text = self._extract_epub_preview(self.temp_epub_path)
            
            # Update preview area
            self.root.after(0, self._update_preview_area, preview_text)
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.log_message(msg, "ERROR"))
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
        """Export the current JSON as an EPUB file."""
        try:
            # Validate JSON first
            json_text = self.json_editor.get(1.0, tk.END).strip()
            if not json_text:
                messagebox.showwarning("Warning", "No JSON content to export")
                return
                
            data = json.loads(json_text)
            
            # Get title for default filename
            title = "book"
            author = "unknown"
            for item in data:
                if item.get('type') == 'title':
                    title = item.get('content', 'book')
                elif item.get('type') == 'author':
                    author = item.get('content', 'unknown')
                    
            default_filename = f"{title} - {author}.epub"
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                title="Export EPUB",
                initialdir=self.default_output_folder,
                initialvalue=default_filename,
                defaultextension=".epub",
                filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
            )
            
            if file_path:
                self.log_message(f"Exporting EPUB to: {file_path}")
                self._generate_epub_from_data(data, file_path)
                messagebox.showinfo("Success", f"EPUB exported successfully to:\n{file_path}")
                
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format:\n{str(e)}")
            self.log_message(f"Export error - JSON parsing: {str(e)}", "ERROR")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export EPUB:\n{str(e)}")
            self.log_message(f"Export error: {str(e)}", "ERROR")
            
    def _generate_epub_from_data(self, book_data, output_path):
        """Generate EPUB from JSON data (adapted from original render.py)."""
        # Create a new EPUB book
        book = epub.EpubBook()
        
        # Set metadata
        title = None
        author = None
        cover_image = None
        
        # Extract title, author, and cover from the JSON data
        for item in book_data:
            if item['type'] == 'title':
                title = item['content']
            elif item['type'] == 'author':
                author = item['content']
            elif item['type'] == 'cover' and 'image' in item:
                cover_image = item['image']
            if title and author and cover_image:
                break
                
        if not title:
            raise ValueError("ebook is missing section 'title'")
        if not author:
            raise ValueError("ebook is missing section 'author'")
        if not cover_image:
            raise ValueError("ebook is missing section 'cover_image'")
            
        book_id = str(uuid.uuid4())
        self.log_message(f"Set id {book_id}")
        book.set_identifier(book_id)
        self.log_message(f"Set title {title}")
        book.set_title(title)
        self.log_message(f"Set language 'en'")
        book.set_language('en')
        self.log_message(f"Set author {author}")
        book.add_author(author)
        
        # Handle cover image
        if self.current_json_file:
            cover_path = os.path.join(os.path.dirname(self.current_json_file), cover_image)
        else:
            cover_path = os.path.join(self.default_input_folder, cover_image)
            
        if os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                cover_content = f.read()
            self.log_message(f"Set cover {cover_path}")
            book.set_cover("cover.png", cover_content)
        else:
            self.log_message(f"Cover image not found: {cover_path}", "WARNING")
            # Create a simple placeholder cover
            placeholder_cover = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00[\x8f\x1c\xa6\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            book.set_cover("cover.png", placeholder_cover)
            
        # Process content into chapters (rest of the logic from original render.py)
        chapters = []
        current_chapter_content = []
        current_chapter_title = "Cover"
        chapter_counter = 0
        division_counter = 0
        image_counter = 1
        
        all_images = []
        
        for item in book_data:
            if item['type'] == 'chapter_header':
                # If we have content for a previous chapter, save it
                if current_chapter_content:
                    if division_counter > 1:
                        chapter = epub.EpubHtml(
                            title=f"{current_chapter_title} - {division_counter}",
                            file_name=f'chapter_{chapter_counter}.xhtml'
                        )
                    else:
                        chapter = epub.EpubHtml(
                            title=current_chapter_title,
                            file_name=f'chapter_{chapter_counter}.xhtml'
                        )
                    chapter.content = ''.join(current_chapter_content)
                    chapters.append(chapter)
                    chapter_counter += 1
                    current_chapter_content = []
                    
                current_chapter_title = f"Chapter {item['content']}"
                current_chapter_content.append(f"<h1>{item['content']}</h1>")
                division_counter = 1
            elif item['type'] in 'title':
                current_chapter_content.append(f"<h1>{item['content']}</h1>")
            elif item['type'] in 'author':
                current_chapter_content.append(f"<h2>{item['content']}</h2>")
            elif item['type'] in ('cover','image') and 'image' in item:
                # Handle images (simplified for preview)
                img_filename = f"image_{image_counter}.png"
                image_counter += 1
                
                # Try to load the actual image
                if self.current_json_file:
                    img_path = os.path.join(os.path.dirname(self.current_json_file), item['image'])
                else:
                    img_path = os.path.join(self.default_input_folder, item['image'])
                    
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        img_content = f.read()
                else:
                    # Use placeholder image
                    img_content = placeholder_cover
                    self.log_message(f"Image not found: {img_path}, using placeholder", "WARNING")
                    
                # Create image item
                img_item = epub.EpubItem(
                    uid=f"image_{len(all_images) + 1}",
                    file_name=f"images/{img_filename}",
                    media_type="image/png",
                    content=img_content
                )
                book.add_item(img_item)
                all_images.append(img_item)
                
                # Add image reference to the chapter content
                caption = item.get('caption', '')
                if caption:
                    current_chapter_content.append(
                        f'<div class="image-container"><img src="images/{img_filename}" alt="{caption}"/><p class="caption">{caption}</p></div>'
                    )
                else:
                    current_chapter_content.append(
                        f'<div class="image-container"><img src="images/{img_filename}" alt="Image"/></div>'
                    )
            else:
                # Build HTML content based on the type
                if item['type'] == 'paragraph':
                    current_chapter_content.append(f"<p>{item['content']}</p>")
                elif item['type'] == 'bold':
                    current_chapter_content.append(f"<p><strong>{item['content']}</strong></p>")
                elif item['type'] == 'block_indent':
                    current_chapter_content.append(f"<blockquote>{item['content']}</blockquote>")
                elif item['type'] == 'sub_header':
                    current_chapter_content.append(f"<h3>{item['content']}</h3>")
                elif item['type'] == 'header':
                    current_chapter_content.append(f"<h2>{item['content']}</h2>")
                elif item['type'] == 'page_division':
                    # If we have content for a previous chapter, save it
                    if current_chapter_content:
                        if division_counter > 1:
                            chapter = epub.EpubHtml(
                                title=f"{current_chapter_title} - {division_counter}",
                                file_name=f'chapter_{chapter_counter}.{division_counter}.xhtml'
                            )
                        else:
                            chapter = epub.EpubHtml(
                                title=current_chapter_title,
                                file_name=f'chapter_{chapter_counter}.{division_counter}.xhtml'
                            )
                        chapter.content = ''.join(current_chapter_content)
                        chapters.append(chapter)
                        current_chapter_content = []
                        
                    division_counter += 1
                    current_chapter_content.append("<hr/>")
                    
        # Add the last chapter if there's content
        if current_chapter_content:
            if division_counter > 1:
                chapter = epub.EpubHtml(
                    title=f"{current_chapter_title} - {division_counter}",
                    file_name=f'chapter_{chapter_counter}.xhtml'
                )
            else:
                chapter = epub.EpubHtml(
                    title=current_chapter_title,
                    file_name=f'chapter_{chapter_counter}.xhtml'
                )
            chapter.content = ''.join(current_chapter_content)
            chapters.append(chapter)
            
        # Add chapters to the book
        for chapter in chapters:
            self.log_message(f"Added chapter {chapter.title}")
            book.add_item(chapter)
            
        # Define TOC
        book.toc = [(epub.Section('Chapters'), chapters)]
        
        # Add default NCX and Nav files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Define CSS style
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
        
        # Create spine
        book.spine = ['nav'] + chapters
        
        # Write the EPUB file
        epub.write_epub(output_path, book, {})
        self.log_message(f"EPUB file created: {output_path}")
        
    def open_epub_in_browser(self):
        """Open the current EPUB in the default browser."""
        if not self.temp_epub_path or not os.path.exists(self.temp_epub_path):
            self.refresh_preview()
            if not self.temp_epub_path:
                messagebox.showwarning("Warning", "No EPUB preview available")
                return
                
        try:
            # For now, just show a message about the EPUB location
            messagebox.showinfo("EPUB Location", f"EPUB preview file:\n{self.temp_epub_path}\n\nYou can open this file with an EPUB reader.")
            self.log_message(f"EPUB preview available at: {self.temp_epub_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open EPUB:\n{str(e)}")
            self.log_message(f"Error opening EPUB: {str(e)}", "ERROR")
            
    def load_default_json(self):
        """Load default JSON file if available."""
        default_path = os.path.join(self.default_input_folder, "book.json")
        if os.path.exists(default_path):
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.json_editor.insert(1.0, json.dumps(data, indent=2))
                self.current_json_file = default_path
                self.current_json_data = data
                self.log_message(f"Loaded default JSON: {default_path}")
                self.refresh_preview()
                
            except Exception as e:
                self.log_message(f"Could not load default JSON: {str(e)}", "WARNING")
                self.new_json()
        else:
            self.new_json()
            
    def check_unsaved_changes(self):
        """Check if there are unsaved changes and prompt user."""
        try:
            current_text = self.json_editor.get(1.0, tk.END).strip()
            if self.current_json_data:
                saved_text = json.dumps(self.current_json_data, indent=2)
                if current_text != saved_text:
                    result = messagebox.askyesnocancel(
                        "Unsaved Changes",
                        "You have unsaved changes. Do you want to save them?"
                    )
                    if result is True:  # Yes
                        self.save_json()
                        return False
                    elif result is False:  # No
                        return False
                    else:  # Cancel
                        return True
        except:
            pass
        return False
        
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About EPUB Render Tool",
            "EPUB Render Tool v1.0\n\n"
            "A GUI tool for editing book JSON data and generating EPUB files.\n\n"
            "Features:\n"
            "• JSON editor with syntax validation\n"
            "• Live EPUB preview\n"
            "• Export to EPUB format\n"
            "• Integrated logging console"
        )
        
    def show_json_help(self):
        """Show JSON format help."""
        help_text = """JSON Format Help

The JSON should be an array of objects, where each object represents a book element:

Required elements:
• {"type": "title", "content": "Book Title"}
• {"type": "author", "content": "Author Name"}
• {"type": "cover", "image": "cover.png"}

Content elements:
• {"type": "chapter_header", "content": "Chapter Number"}
• {"type": "paragraph", "content": "Text content"}
• {"type": "header", "content": "Section header"}
• {"type": "sub_header", "content": "Subsection header"}
• {"type": "bold", "content": "Bold text"}
• {"type": "block_indent", "content": "Indented block"}
• {"type": "image", "image": "image.png", "caption": "Optional caption"}
• {"type": "page_division"} - Creates a page break

Images should be relative paths from the JSON file location.

Auto-Stub Feature:
When you validate JSON and required sections are missing, the application will offer to automatically insert stub entries with placeholder content. This helps ensure your JSON has all necessary elements for EPUB generation.
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("JSON Format Help")
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
    app = RenderGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.check_unsaved_changes():
            return
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()


if __name__ == "__main__":
    main()