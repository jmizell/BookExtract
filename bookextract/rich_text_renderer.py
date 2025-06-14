"""
Rich Text Renderer Module

This module provides shared classes for rendering rich text previews of book content.
It can be used by both the edit GUI and EPUB renderer to provide consistent,
high-quality text formatting and image display.
"""

import tkinter as tk
import os
import json
from typing import List, Tuple, Dict, Any, Optional, Union
from PIL import Image, ImageTk
from pathlib import Path


class ImageManager:
    """Manages image loading, caching, and resizing for rich text display."""
    
    def __init__(self, logger=None):
        """Initialize the image manager.
        
        Args:
            logger: Optional logging function that takes (message, level) parameters
        """
        self.image_cache = {}
        self.logger = logger
        
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message if logger is available."""
        if self.logger:
            self.logger(message, level)
    
    def clear_cache(self):
        """Clear the image cache to free memory."""
        self.image_cache.clear()
        
    def load_and_resize_image(self, image_path: str, max_width: int = 400, 
                            max_height: int = 300, is_cover: bool = False) -> Optional[tk.PhotoImage]:
        """Load and resize an image for display in the preview.
        
        Args:
            image_path: Path to the image file
            max_width: Maximum width for the resized image
            max_height: Maximum height for the resized image
            is_cover: If True, use larger dimensions for cover images
            
        Returns:
            PhotoImage object or None if loading fails
        """
        try:
            # Use larger dimensions for cover images
            if is_cover:
                max_width = 300
                max_height = 400
            
            # Check cache first
            cache_key = f"{image_path}_{max_width}_{max_height}_{is_cover}"
            if cache_key in self.image_cache:
                return self.image_cache[cache_key]
            
            # Load and process image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (handles RGBA, P mode, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Calculate resize dimensions maintaining aspect ratio
                img_width, img_height = img.size
                width_ratio = max_width / img_width
                height_ratio = max_height / img_height
                ratio = min(width_ratio, height_ratio)
                
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                
                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img_resized)
                
                # Cache the result
                self.image_cache[cache_key] = photo
                
                return photo
                
        except Exception as e:
            self.log_message(f"Failed to load image {image_path}: {str(e)}", "WARNING")
            return None


class RichTextFormatter:
    """Handles text tag configuration and formatting for rich text display."""
    
    def __init__(self, text_widget: tk.Text):
        """Initialize the formatter with a text widget.
        
        Args:
            text_widget: The tkinter Text widget to configure
        """
        self.text_widget = text_widget
        self.setup_text_tags()
    
    def setup_text_tags(self):
        """Configure text tags for rich formatting in the text widget."""
        # Title formatting
        self.text_widget.tag_configure("title", 
                                     font=("Georgia", 24, "bold"), 
                                     justify="center",
                                     spacing1=20, spacing3=20)
        
        # Author formatting
        self.text_widget.tag_configure("author", 
                                     font=("Georgia", 16, "italic"), 
                                     justify="center",
                                     spacing3=30)
        
        # Chapter header formatting
        self.text_widget.tag_configure("chapter_header", 
                                     font=("Georgia", 20, "bold"), 
                                     justify="center",
                                     spacing1=30, spacing3=20)
        
        # Header formatting (h2)
        self.text_widget.tag_configure("header", 
                                     font=("Georgia", 16, "bold"), 
                                     spacing1=15, spacing3=10)
        
        # Sub-header formatting (h3)
        self.text_widget.tag_configure("sub_header", 
                                     font=("Georgia", 14, "bold"), 
                                     spacing1=10, spacing3=5)
        
        # Paragraph formatting
        self.text_widget.tag_configure("paragraph", 
                                     font=("Georgia", 11), 
                                     spacing1=5, spacing3=5,
                                     lmargin1=20, lmargin2=20)
        
        # Bold text formatting
        self.text_widget.tag_configure("bold", 
                                     font=("Georgia", 11, "bold"), 
                                     spacing1=5, spacing3=5,
                                     lmargin1=20, lmargin2=20)
        
        # Block indent formatting
        self.text_widget.tag_configure("block_indent", 
                                     font=("Georgia", 11, "italic"), 
                                     spacing1=5, spacing3=5,
                                     lmargin1=40, lmargin2=40,
                                     rmargin=40)
        
        # Image placeholder formatting
        self.text_widget.tag_configure("image", 
                                     font=("Georgia", 10, "italic"), 
                                     justify="center",
                                     spacing1=10, spacing3=10,
                                     background="#f0f0f0")
        
        # Image caption formatting
        self.text_widget.tag_configure("image_caption", 
                                     font=("Georgia", 9, "italic"), 
                                     justify="center",
                                     spacing3=15)
        
        # Cover formatting
        self.text_widget.tag_configure("cover", 
                                     font=("Georgia", 12, "bold"), 
                                     justify="center",
                                     spacing1=20, spacing3=20,
                                     background="#e8e8e8")
        
        # Horizontal rule formatting
        self.text_widget.tag_configure("hr", 
                                     font=("Georgia", 8), 
                                     justify="center",
                                     spacing1=15, spacing3=15)


class ContentProcessor:
    """Processes book content data into rich text format."""
    
    def __init__(self, image_manager: ImageManager, base_path: str = "", logger=None):
        """Initialize the content processor.
        
        Args:
            image_manager: ImageManager instance for handling images
            base_path: Base path for resolving relative image paths
            logger: Optional logging function
        """
        self.image_manager = image_manager
        self.base_path = base_path
        self.logger = logger
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message if logger is available."""
        if self.logger:
            self.logger(message, level)
    
    def process_json_data(self, book_data: List[Dict[str, Any]]) -> List[Tuple[str, Union[str, tk.PhotoImage]]]:
        """Process JSON book data into rich text content parts.
        
        Args:
            book_data: List of content items from JSON
            
        Returns:
            List of (tag, content) tuples for rich text display
        """
        content_parts = []
        
        for item in book_data:
            item_type = item.get('type', '')
            content = item.get('content', '')
            
            if item_type == 'title':
                content_parts.append(('title', content))
                content_parts.append(('paragraph', ''))  # Add spacing
                
            elif item_type == 'author':
                content_parts.append(('author', f"by {content}"))
                content_parts.append(('paragraph', ''))  # Add spacing
                
            elif item_type == 'cover':
                self._process_cover_image(item, content_parts)
                
            elif item_type == 'chapter_header':
                content_parts.append(('paragraph', ''))  # Add spacing before chapter
                content_parts.append(('chapter_header', f"Chapter {content}"))
                content_parts.append(('paragraph', ''))  # Add spacing after chapter
                
            elif item_type == 'header':
                content_parts.append(('header', content))
                
            elif item_type == 'sub_header':
                content_parts.append(('sub_header', content))
                
            elif item_type == 'paragraph':
                content_parts.append(('paragraph', content))
                
            elif item_type == 'bold':
                content_parts.append(('bold', content))
                
            elif item_type == 'block_indent':
                content_parts.append(('block_indent', content))
                
            elif item_type == 'image':
                self._process_content_image(item, content_parts)
                    
            elif item_type == 'page_division':
                content_parts.append(('hr', '─' * 50))
                content_parts.append(('paragraph', ''))  # Add spacing
                
            else:
                # Unknown type, render as paragraph
                content_parts.append(('paragraph', f"[{item_type.upper()}]: {content}"))
        
        return content_parts
    
    def process_intermediate_data(self, intermediate_data) -> List[Tuple[str, Union[str, tk.PhotoImage]]]:
        """Process BookIntermediate data into rich text content parts.
        
        Args:
            intermediate_data: BookIntermediate instance
            
        Returns:
            List of (tag, content) tuples for rich text display
        """
        content_parts = []
        
        # Add title and author from metadata
        if intermediate_data.metadata.title:
            content_parts.append(('title', intermediate_data.metadata.title))
            content_parts.append(('paragraph', ''))
        
        if intermediate_data.metadata.author:
            content_parts.append(('author', f"by {intermediate_data.metadata.author}"))
            content_parts.append(('paragraph', ''))
        
        # Add cover if available
        if intermediate_data.metadata.cover_image:
            cover_item = {'type': 'cover', 'image': intermediate_data.metadata.cover_image}
            self._process_cover_image(cover_item, content_parts)
        
        # Process chapters
        for chapter in intermediate_data.chapters:
            # Add chapter header
            content_parts.append(('paragraph', ''))
            content_parts.append(('chapter_header', f"Chapter {chapter.number}: {chapter.title}"))
            content_parts.append(('paragraph', ''))
            
            # Process chapter sections
            for section in chapter.sections:
                section_dict = section.to_dict()
                section_type = section_dict.get('type', '')
                section_content = section_dict.get('content', '')
                
                if section_type == 'paragraph':
                    content_parts.append(('paragraph', section_content))
                elif section_type == 'header':
                    content_parts.append(('header', section_content))
                elif section_type == 'sub_header':
                    content_parts.append(('sub_header', section_content))
                elif section_type == 'bold':
                    content_parts.append(('bold', section_content))
                elif section_type == 'block_indent':
                    content_parts.append(('block_indent', section_content))
                elif section_type == 'image':
                    self._process_content_image(section_dict, content_parts)
                else:
                    # Default to paragraph for unknown types
                    content_parts.append(('paragraph', section_content))
        
        return content_parts
    
    def _process_cover_image(self, item: Dict[str, Any], content_parts: List[Tuple[str, Union[str, tk.PhotoImage]]]):
        """Process a cover image item."""
        image_path = item.get('image', '')
        if image_path:
            full_image_path = self._resolve_image_path(image_path)
            
            if os.path.exists(full_image_path):
                # Try to load the actual image
                photo = self.image_manager.load_and_resize_image(full_image_path, is_cover=True)
                if photo:
                    content_parts.append(('cover_image', photo))
                else:
                    content_parts.append(('cover', f"[COVER IMAGE: {image_path} - LOAD FAILED]"))
            else:
                content_parts.append(('cover', f"[COVER IMAGE: {image_path} - NOT FOUND]"))
        else:
            content_parts.append(('cover', "[COVER IMAGE: No image specified]"))
        content_parts.append(('paragraph', ''))  # Add spacing
    
    def _process_content_image(self, item: Dict[str, Any], content_parts: List[Tuple[str, Union[str, tk.PhotoImage]]]):
        """Process a content image item."""
        image_path = item.get('image', '')
        caption = item.get('caption', '')
        
        if image_path:
            full_image_path = self._resolve_image_path(image_path)
            
            if os.path.exists(full_image_path):
                # Try to load the actual image
                photo = self.image_manager.load_and_resize_image(full_image_path, is_cover=False)
                if photo:
                    content_parts.append(('content_image', photo))
                else:
                    content_parts.append(('image', f"[IMAGE: {image_path} - LOAD FAILED]"))
            else:
                content_parts.append(('image', f"[IMAGE: {image_path} - NOT FOUND]"))
        else:
            content_parts.append(('image', "[IMAGE: No image specified]"))
        
        if caption:
            content_parts.append(('image_caption', caption))
    
    def _resolve_image_path(self, image_path: str) -> str:
        """Resolve relative image path to absolute path."""
        if os.path.isabs(image_path):
            return image_path
        return os.path.join(self.base_path, image_path)


class RichTextRenderer:
    """Main class that coordinates rich text rendering with images."""
    
    def __init__(self, text_widget: tk.Text, base_path: str = "", logger=None):
        """Initialize the rich text renderer.
        
        Args:
            text_widget: The tkinter Text widget to render into
            base_path: Base path for resolving relative image paths
            logger: Optional logging function that takes (message, level) parameters
        """
        self.text_widget = text_widget
        self.base_path = base_path
        self.logger = logger
        
        # Initialize components
        self.image_manager = ImageManager(logger)
        self.formatter = RichTextFormatter(text_widget)
        self.processor = ContentProcessor(self.image_manager, base_path, logger)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message if logger is available."""
        if self.logger:
            self.logger(message, level)
    
    def clear_image_cache(self):
        """Clear the image cache to free memory."""
        self.image_manager.clear_cache()
    
    def set_base_path(self, base_path: str):
        """Update the base path for image resolution."""
        self.base_path = base_path
        self.processor.base_path = base_path
    
    def render_json_data(self, book_data: List[Dict[str, Any]]):
        """Render JSON book data as rich text.
        
        Args:
            book_data: List of content items from JSON
        """
        try:
            # Process data into content parts
            content_parts = self.processor.process_json_data(book_data)
            
            # Render content parts
            self._render_content_parts(content_parts)
            
            self.log_message("Rich text preview updated successfully")
            
        except Exception as e:
            self.log_message(f"Error rendering JSON data: {str(e)}", "ERROR")
            raise
    
    def render_intermediate_data(self, intermediate_data):
        """Render BookIntermediate data as rich text.
        
        Args:
            intermediate_data: BookIntermediate instance
        """
        try:
            # Process data into content parts
            content_parts = self.processor.process_intermediate_data(intermediate_data)
            
            # Render content parts
            self._render_content_parts(content_parts)
            
            self.log_message("Rich text preview updated successfully")
            
        except Exception as e:
            self.log_message(f"Error rendering intermediate data: {str(e)}", "ERROR")
            raise
    
    def _render_content_parts(self, content_parts: List[Tuple[str, Union[str, tk.PhotoImage]]]):
        """Render content parts into the text widget."""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        
        for tag, content in content_parts:
            if tag in ('cover_image', 'content_image'):
                # Handle image content
                if content:  # content is a PhotoImage object
                    # Insert a newline before the image for spacing
                    self.text_widget.insert(tk.INSERT, '\n')
                    
                    # Insert the image
                    self.text_widget.image_create(tk.INSERT, image=content)
                    
                    # Insert a newline after the image
                    self.text_widget.insert(tk.INSERT, '\n')
            else:
                # Handle text content
                if content:  # Only insert non-empty text
                    start_pos = self.text_widget.index(tk.INSERT)
                    self.text_widget.insert(tk.INSERT, content + '\n')
                    end_pos = self.text_widget.index(tk.INSERT)
                    
                    # Apply the tag to the inserted text
                    self.text_widget.tag_add(tag, start_pos, end_pos)
        
        self.text_widget.config(state=tk.DISABLED)