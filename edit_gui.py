#!/usr/bin/env python3
"""
Book Renderer GUI - A tkinter interface for editing and previewing book intermediate format.

This application provides a user-friendly interface to edit book JSON data
and preview the rendered content as formatted rich text.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import threading
from pathlib import Path
from PIL import Image, ImageTk
from bookextract import BookIntermediate, BookConverter, RichTextRenderer

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

class RenderBookGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Renderer Tool")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # State variables
        self.current_json_file = None
        self.current_json_data = None
        self.is_rendering = False
        self.render_thread = None
        
        # Default values
        self.default_input_folder = str(Path.cwd() / "out")
        self.default_output_folder = str(Path.cwd() / "out")
        
        # Rich text renderer will be initialized after UI setup
        self.rich_text_renderer = None
        
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
        file_menu.add_command(label="Open Intermediate...", command=self.open_intermediate)
        file_menu.add_separator()
        file_menu.add_command(label="Save JSON", command=self.save_json, accelerator="Ctrl+S")
        file_menu.add_command(label="Save JSON As...", command=self.save_json_as, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="Save Intermediate As...", command=self.save_intermediate_as)
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
        self.root.bind('<Control-f>', lambda e: self.format_json())
        self.root.bind('<Control-v>', lambda e: self.validate_json())
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
        self.json_editor = tk.Text(
            left_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            undo=True,
            maxundo=50,
            background="white",
            foreground="black"
        )
        self.json_editor.grid(row=1, column=0, sticky="nsew")

        # Configure tags for syntax highlighting
        self.init_syntax_highlighting()
        
        # Right panel - Rich Text Preview
        right_frame = ttk.LabelFrame(main_frame, text="Rich Text Preview", padding="5")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Preview toolbar
        preview_toolbar = ttk.Frame(right_frame)
        preview_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(preview_toolbar, text="Refresh", command=self.refresh_preview).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(preview_toolbar, text="Save Intermediate", command=self.save_intermediate_as).pack(side=tk.LEFT, padx=(0, 2))
        
        # Rich text preview area
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
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_console.insert(tk.END, f"[{timestamp}] {level}: {message}\n")
        self.log_console.see(tk.END)
        self.log_console.config(state=tk.DISABLED)

    def init_syntax_highlighting(self):
        """Initialize syntax highlighting for the JSON editor."""
        self.json_editor.tag_configure("Token.Keyword", foreground="#007020")
        self.json_editor.tag_configure("Token.Keyword.Constant", foreground="#007020")
        self.json_editor.tag_configure("Token.Name.Tag", foreground="#007020")
        self.json_editor.tag_configure("Token.Literal.String", foreground="#BA2121")
        self.json_editor.tag_configure("Token.Literal.String.Double", foreground="#BA2121")
        self.json_editor.tag_configure("Token.Literal.Number", foreground="#6897BB")
        self.json_editor.tag_configure("Token.Punctuation", foreground="#000000")
        self.json_editor.tag_configure("Token.Name.Builtin", foreground="#008080")
        self.json_editor.tag_configure("Token.Name.Function", foreground="#0000FF")
        self.json_editor.tag_configure("Token.Name.Class", foreground="#0000FF")
        self.json_editor.tag_configure("Token.Name.Exception", foreground="#D2413A")
        self.json_editor.tag_configure("Token.Comment", foreground="#BBBBBB")

    def highlight_json(self, json_text):
        """Highlight the JSON code in the editor."""
        self.json_editor.tag_remove("Token.Keyword", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Keyword.Constant", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Name.Tag", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Literal.String", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Literal.String.Double", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Literal.Number", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Punctuation", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Name.Builtin", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Name.Function", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Name.Class", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Name.Exception", "1.0", tk.END)
        self.json_editor.tag_remove("Token.Comment", "1.0", tk.END)

        lexer = JsonLexer()
        formatter = HtmlFormatter()
        html = highlight(json_text, lexer, formatter)

        start = "1.0"
        for line in html.splitlines():
            if line.strip():
                parts = line.split("</span>")
                for part in parts:
                    if "<span" in part:
                        tag = part.split("<span ")[1].split(">")[0]
                        text = part.split(">")[1]
                        self.json_editor.insert(start, text)
                        end = f"{start}+{len(text)}c"
                        self.json_editor.tag_add(tag, start, end)
                        start = end
                    else:
                        self.json_editor.insert(start, part)
                        end = f"{start}+{len(part)}c"
                        start = end

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
        self.highlight_json(self.json_editor.get("1.0", tk.END))
        
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
                self.highlight_json(self.json_editor.get("1.0", tk.END))
                
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
    
    def open_intermediate(self):
        """Open an intermediate representation file."""
        if self.check_unsaved_changes():
            return
            
        file_path = filedialog.askopenfilename(
            title="Open Intermediate File",
            initialdir=self.default_input_folder,
            filetypes=[("Intermediate files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Load intermediate representation
                intermediate = BookIntermediate.load_from_file(file_path)
                
                # Convert to section array format for editing
                sections = BookConverter.to_section_array(intermediate)
                
                self.json_editor.delete(1.0, tk.END)
                self.json_editor.insert(1.0, json.dumps(sections, indent=2))
                self.current_json_file = file_path
                self.current_json_data = sections
                self.log_message(f"Opened intermediate file: {file_path}")
                self.log_message(f"Loaded {intermediate.get_chapter_count()} chapters, {intermediate.get_total_word_count()} words")
                self.refresh_preview()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open intermediate file:\n{str(e)}")
                self.log_message(f"Error opening intermediate file: {str(e)}", "ERROR")
    
    def save_intermediate_as(self):
        """Save the current JSON as an intermediate representation file."""
        try:
            # Validate JSON first
            json_text = self.json_editor.get(1.0, tk.END).strip()
            if not json_text:
                messagebox.showwarning("Warning", "No JSON content to save")
                return
                
            sections = json.loads(json_text)
            
            # Convert to intermediate representation
            intermediate = BookConverter.from_section_array(sections)
            
            # Get title for default filename
            default_filename = f"{intermediate.metadata.title} - {intermediate.metadata.author}.intermediate.json"
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                title="Save Intermediate File",
                initialdir=self.default_output_folder,
                initialfile=default_filename,
                defaultextension=".json",
                filetypes=[("Intermediate files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                intermediate.save_to_file(file_path)
                self.log_message(f"Saved intermediate representation to: {file_path}")
                self.log_message(f"Saved {intermediate.get_chapter_count()} chapters, {intermediate.get_total_word_count()} words")
                messagebox.showinfo("Success", f"Intermediate representation saved to:\n{file_path}")
                
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format:\n{str(e)}")
            self.log_message(f"Save intermediate error - JSON parsing: {str(e)}", "ERROR")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save intermediate file:\n{str(e)}")
            self.log_message(f"Save intermediate error: {str(e)}", "ERROR")
            
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
                        # Determine cover image path based on current JSON file location
                        if self.current_json_file:
                            # Use the same name as JSON file but with .png extension
                            json_path = Path(self.current_json_file)
                            cover_image = json_path.stem + ".png"
                        else:
                            # Default fallback if no file is loaded
                            cover_image = "cover.png"
                            
                        new_data.append({
                            "type": "cover",
                            "image": cover_image
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
            self.highlight_json(self.json_editor.get("1.0", tk.END))
                
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format:\n{str(e)}")
            self.log_message(f"JSON validation error: {str(e)}", "ERROR")
            
    def refresh_preview(self):
        """Refresh the rich text preview."""
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
            
            # Parse JSON
            json_text = self.json_editor.get(1.0, tk.END).strip()
            if not json_text:
                self.log_message("No JSON content to preview", "WARNING")
                return
                
            data = json.loads(json_text)
            
            # Update base path for image resolution
            if self.rich_text_renderer:
                if self.current_json_file:
                    base_path = os.path.dirname(self.current_json_file)
                else:
                    base_path = self.default_input_folder
                self.rich_text_renderer.set_base_path(base_path)
                
                # Render using the shared renderer
                self.root.after(0, self._render_preview, data)
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.log_message(msg, "ERROR"))
        except Exception as e:
            error_msg = f"Preview generation error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.log_message(msg, "ERROR"))
        finally:
            self.is_rendering = False
            
    def _render_preview(self, data):
        """Render the preview using the RichTextRenderer."""
        try:
            if self.rich_text_renderer:
                self.rich_text_renderer.render_json_data(data)
        except Exception as e:
            self.log_message(f"Rendering error: {str(e)}", "ERROR")

        
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
            "About Book Renderer Tool",
            "Book Renderer Tool v1.0\n\n"
            "A GUI tool for editing book JSON data and previewing as rich text.\n\n"
            "Features:\n"
            "• JSON editor with syntax validation\n"
            "• Rich text preview with formatting\n"
            "• Intermediate format support\n"
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
• {"type": "page_division"} - Creates a horizontal rule

Images should be relative paths from the JSON file location.

Rich Text Preview:
The right panel shows your content formatted as rich text with:
• Styled headings and titles
• Proper spacing and indentation
• Actual image rendering (PNG, JPEG, GIF, BMP supported)
• Image placeholders for missing or invalid images
• Visual separation between sections

Auto-Stub Feature:
When you validate JSON and required sections are missing, the application will offer to automatically insert stub entries with placeholder content.
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
    app = RenderBookGUI(root)
    
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