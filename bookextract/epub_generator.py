"""
EPUB Generation Module

This module handles the creation of EPUB files from section array data.
It provides a modular EPUB generation class that can be used by GUI or CLI interfaces.
"""

import os
import uuid
from ebooklib import epub


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