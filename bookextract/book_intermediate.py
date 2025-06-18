"""
Book Intermediate Representation

This module provides a unified intermediate representation for book content
that can be used by both EPUB and M4B generation pipelines.

The intermediate format bridges the gap between:
1. EPUB extraction output (book_info.json format)
2. Render GUI input (section array format)
3. Output formats (EPUB, M4B)
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import re
import html
from ebooklib import epub
from bs4 import BeautifulSoup


@dataclass
class BookMetadata:
    """Book metadata information."""
    title: str
    author: str
    language: str = "en"
    identifier: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    creation_date: Optional[str] = None
    
    def __post_init__(self):
        if self.identifier is None:
            self.identifier = str(uuid.uuid4())
        if self.creation_date is None:
            self.creation_date = datetime.now().isoformat()


@dataclass
class ContentSection:
    """A section of content within a chapter."""
    type: str  # paragraph, header, sub_header, bold, block_indent, image, etc.
    content: Optional[str] = None
    image: Optional[str] = None
    caption: Optional[str] = None
    source: Optional[str] = None  # Source file/page for debugging
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {"type": self.type}
        if self.content is not None:
            result["content"] = self.content
        if self.image is not None:
            result["image"] = self.image
        if self.caption is not None:
            result["caption"] = self.caption
        if self.source is not None:
            result["source"] = self.source
        return result


@dataclass
class Chapter:
    """A book chapter containing multiple content sections."""
    number: int
    title: str
    sections: List[ContentSection]
    filename: Optional[str] = None
    
    def get_text_content(self) -> str:
        """Extract all text content from the chapter."""
        text_parts = []
        for section in self.sections:
            if section.content:
                text_parts.append(section.content)
        return "\n\n".join(text_parts)
    
    def get_word_count(self) -> int:
        """Get approximate word count for the chapter."""
        text = self.get_text_content()
        return len(text.split()) if text else 0


@dataclass
class BookIntermediate:
    """Intermediate representation of a book."""
    metadata: BookMetadata
    chapters: List[Chapter]
    
    def get_total_word_count(self) -> int:
        """Get total word count for the book."""
        return sum(chapter.get_word_count() for chapter in self.chapters)
    
    def get_chapter_count(self) -> int:
        """Get total number of chapters."""
        return len(self.chapters)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metadata": asdict(self.metadata),
            "chapters": [
                {
                    "number": chapter.number,
                    "title": chapter.title,
                    "filename": chapter.filename,
                    "sections": [section.to_dict() for section in chapter.sections],
                    "word_count": chapter.get_word_count()
                }
                for chapter in self.chapters
            ],
            "total_chapters": self.get_chapter_count(),
            "total_word_count": self.get_total_word_count(),
            "format_version": "1.0"
        }
    
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save the intermediate representation to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'BookIntermediate':
        """Load intermediate representation from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookIntermediate':
        """Create BookIntermediate from dictionary."""
        metadata = BookMetadata(**data["metadata"])
        
        chapters = []
        for chapter_data in data["chapters"]:
            sections = []
            for section_data in chapter_data["sections"]:
                sections.append(ContentSection(**section_data))
            
            chapter = Chapter(
                number=chapter_data["number"],
                title=chapter_data["title"],
                sections=sections,
                filename=chapter_data.get("filename")
            )
            chapters.append(chapter)
        
        return cls(metadata=metadata, chapters=chapters)


class BookConverter:
    """Converter between different book formats and the intermediate representation."""
    
    @staticmethod
    def from_epub_extractor(book_info_path: Union[str, Path], 
                          text_files_dir: Optional[Union[str, Path]] = None) -> BookIntermediate:
        """
        Convert from epub_extractor output format to intermediate representation.
        
        Args:
            book_info_path: Path to book_info.json file
            text_files_dir: Directory containing chapter text files (optional)
        """
        with open(book_info_path, 'r', encoding='utf-8') as f:
            book_info = json.load(f)
        
        # Extract metadata
        metadata_dict = book_info["metadata"]
        metadata = BookMetadata(
            title=metadata_dict["title"],
            author=metadata_dict["author"],
            language=metadata_dict.get("language", "en"),
            identifier=metadata_dict.get("identifier")
        )
        
        # Convert chapters
        chapters = []
        for chapter_info in book_info["chapters"]:
            # Create a single paragraph section for each chapter
            # This is a simplified conversion - could be enhanced to parse content structure
            sections = [
                ContentSection(
                    type="chapter_header",
                    content=chapter_info["title"]
                ),
                ContentSection(
                    type="paragraph",
                    content=chapter_info["content"]
                )
            ]
            
            chapter = Chapter(
                number=chapter_info["number"],
                title=chapter_info["title"],
                sections=sections,
                filename=chapter_info.get("filename")
            )
            chapters.append(chapter)
        
        return BookIntermediate(metadata=metadata, chapters=chapters)
    
    @staticmethod
    def from_section_array(sections: List[Dict[str, Any]], 
                          base_path: Optional[Union[str, Path]] = None) -> BookIntermediate:
        """
        Convert from render_gui section array format to intermediate representation.
        
        Args:
            sections: List of section dictionaries
            base_path: Base path for resolving relative image paths
        """
        # Extract metadata from sections
        title = None
        author = None
        cover_image = None
        
        for section in sections:
            if section["type"] == "title":
                title = section["content"]
            elif section["type"] == "author":
                author = section["content"]
            elif section["type"] == "cover" and "image" in section:
                cover_image = section["image"]
        
        if not title:
            raise ValueError("Missing required 'title' section")
        if not author:
            raise ValueError("Missing required 'author' section")
        
        metadata = BookMetadata(
            title=title,
            author=author,
            cover_image=cover_image
        )
        
        # Process sections into chapters
        chapters = []
        current_chapter_sections = []
        current_chapter_title = "Introduction"
        chapter_number = 0
        
        for section in sections:
            section_type = section["type"]
            
            if section_type == "chapter_header":
                # Save previous chapter if it has content
                if current_chapter_sections:
                    chapter = Chapter(
                        number=chapter_number,
                        title=current_chapter_title,
                        sections=current_chapter_sections.copy()
                    )
                    chapters.append(chapter)
                    current_chapter_sections = []
                
                # Start new chapter
                chapter_number += 1
                current_chapter_title = f"Chapter {section['content']}"
                current_chapter_sections.append(ContentSection(
                    type="chapter_header",
                    content=section["content"]
                ))
            
            elif section_type in ["title", "author", "cover"]:
                # Skip metadata sections as they're already processed
                continue
            
            elif section_type == "page_division":
                # Add page break marker
                current_chapter_sections.append(ContentSection(type="page_division"))
            
            else:
                # Regular content section
                content_section = ContentSection(
                    type=section_type,
                    content=section.get("content"),
                    image=section.get("image"),
                    caption=section.get("caption"),
                    source=section.get("source")
                )
                current_chapter_sections.append(content_section)
        
        # Add the last chapter
        if current_chapter_sections:
            chapter = Chapter(
                number=chapter_number if chapter_number > 0 else 1,
                title=current_chapter_title,
                sections=current_chapter_sections
            )
            chapters.append(chapter)
        
        # If no chapters were created, create a single chapter with all content
        if not chapters:
            all_sections = []
            for section in sections:
                if section["type"] not in ["title", "author", "cover"]:
                    all_sections.append(ContentSection(
                        type=section["type"],
                        content=section.get("content"),
                        image=section.get("image"),
                        caption=section.get("caption"),
                        source=section.get("source")
                    ))
            
            if all_sections:
                chapters.append(Chapter(
                    number=1,
                    title="Chapter 1",
                    sections=all_sections
                ))
        
        return BookIntermediate(metadata=metadata, chapters=chapters)
    
    @staticmethod
    def to_section_array(book: BookIntermediate) -> List[Dict[str, Any]]:
        """
        Convert intermediate representation to render_gui section array format.
        """
        sections = []
        
        # Add metadata sections
        sections.append({"type": "title", "content": book.metadata.title})
        sections.append({"type": "author", "content": book.metadata.author})
        
        if book.metadata.cover_image:
            sections.append({"type": "cover", "image": book.metadata.cover_image})
        
        # Add chapter content
        for chapter in book.chapters:
            for section in chapter.sections:
                sections.append(section.to_dict())
        
        return sections
    
    @staticmethod
    def from_epub_file(epub_path: Union[str, Path], 
                      extract_images: bool = True,
                      output_dir: Optional[Union[str, Path]] = None) -> BookIntermediate:
        """
        Convert EPUB file to intermediate representation.
        
        Args:
            epub_path: Path to the EPUB file
            extract_images: Whether to extract images from the EPUB
            output_dir: Directory to extract images to (defaults to same dir as EPUB)
        """
        epub_path = Path(epub_path)
        if output_dir is None:
            output_dir = epub_path.parent
        else:
            output_dir = Path(output_dir)
        
        # Read the EPUB file
        book = epub.read_epub(str(epub_path))
        
        # Extract metadata
        title = book.get_metadata('DC', 'title')
        title = title[0][0] if title else "Unknown Title"
        
        author = book.get_metadata('DC', 'creator')
        author = author[0][0] if author else "Unknown Author"
        
        language = book.get_metadata('DC', 'language')
        language = language[0][0] if language else "en"
        
        identifier = book.get_metadata('DC', 'identifier')
        identifier = identifier[0][0] if identifier else None
        
        # Extract cover image if available
        cover_image = None
        if extract_images:
            cover_item = None
            for item in book.get_items():
                # Look for cover image (type 10 is cover image, type 1 is regular image)
                if (item.get_type() == 10 and 'cover' in item.get_name().lower()) or \
                   (item.get_type() == 1 and 'cover' in item.get_name().lower()):
                    cover_item = item
                    break
            
            if cover_item:
                cover_filename = f"cover_{epub_path.stem}.png"
                cover_path = output_dir / cover_filename
                with open(cover_path, 'wb') as f:
                    f.write(cover_item.get_content())
                cover_image = cover_filename
        
        metadata = BookMetadata(
            title=title,
            author=author,
            language=language,
            identifier=identifier,
            cover_image=cover_image
        )
        
        # Extract chapters and content
        chapters = []
        chapter_number = 0
        
        # Get all HTML items in reading order
        html_items = []
        for item in book.get_items():
            # Type 9 is HTML document
            if item.get_type() == 9:
                html_items.append(item)
        
        # Sort by spine order if available
        spine_order = [item[0] for item in book.spine]
        html_items.sort(key=lambda x: spine_order.index(x.get_id()) if x.get_id() in spine_order else 999)
        
        # Process each HTML document
        for item in html_items:
            content = item.get_content().decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract sections from the HTML
            sections = BookConverter._extract_sections_from_html(soup, extract_images, output_dir, epub_path.stem)
            
            if sections:
                chapter_number += 1
                # Try to get chapter title from the first heading or use filename
                chapter_title = BookConverter._extract_chapter_title(soup) or f"Chapter {chapter_number}"
                
                chapter = Chapter(
                    number=chapter_number,
                    title=chapter_title,
                    sections=sections,
                    filename=item.get_name()
                )
                chapters.append(chapter)
        
        return BookIntermediate(metadata=metadata, chapters=chapters)
    
    @staticmethod
    def _extract_chapter_title(soup: BeautifulSoup) -> Optional[str]:
        """Extract chapter title from HTML soup."""
        # Look for headings in order of preference
        for tag in ['h1', 'h2', 'h3', 'title']:
            element = soup.find(tag)
            if element and element.get_text().strip():
                return element.get_text().strip()
        return None
    
    @staticmethod
    def _extract_sections_from_html(soup: BeautifulSoup, 
                                   extract_images: bool,
                                   output_dir: Path,
                                   epub_stem: str) -> List[ContentSection]:
        """Extract content sections from HTML soup."""
        sections = []
        image_counter = 1
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Process elements in document order
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'blockquote', 'img']):
            text = element.get_text().strip()
            
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Handle headings
                if element.name == 'h1':
                    if text and not any(keyword in text.lower() for keyword in ['chapter', 'part']):
                        sections.append(ContentSection(type="header", content=text))
                    elif text and any(keyword in text.lower() for keyword in ['chapter', 'part']):
                        # Extract chapter number/identifier
                        chapter_match = re.search(r'(?:chapter|part)\s*(\d+|[ivxlcdm]+)', text.lower())
                        if chapter_match:
                            sections.append(ContentSection(type="chapter_header", content=chapter_match.group(1)))
                        else:
                            sections.append(ContentSection(type="chapter_header", content=text))
                elif element.name == 'h2':
                    if text:
                        sections.append(ContentSection(type="header", content=text))
                else:  # h3, h4, h5, h6
                    if text:
                        sections.append(ContentSection(type="sub_header", content=text))
            
            elif element.name == 'img' and extract_images:
                # Handle images
                src = element.get('src')
                alt = element.get('alt', '')
                if src:
                    # Try to find the image in the EPUB
                    image_filename = f"image_{epub_stem}_{image_counter}.png"
                    image_counter += 1
                    sections.append(ContentSection(
                        type="image",
                        image=image_filename,
                        caption=alt if alt else None
                    ))
            
            elif element.name in ['p', 'div']:
                # Handle paragraphs and divs
                if text:
                    # Check if it's bold/strong content
                    if element.find(['b', 'strong']) and len(element.find_all(['b', 'strong'])) == 1:
                        strong_text = element.find(['b', 'strong']).get_text().strip()
                        if strong_text == text:  # Entire paragraph is bold
                            sections.append(ContentSection(type="bold", content=text))
                            continue
                    
                    # Check if it's indented content
                    style = element.get('style', '')
                    css_class = element.get('class', [])
                    if ('margin-left' in style or 'text-indent' in style or 
                        any('indent' in cls.lower() for cls in css_class if isinstance(cls, str))):
                        sections.append(ContentSection(type="block_indent", content=text))
                    else:
                        sections.append(ContentSection(type="paragraph", content=text))
            
            elif element.name == 'blockquote':
                # Handle blockquotes
                if text:
                    sections.append(ContentSection(type="block_indent", content=text))
        
        return sections
    
    @staticmethod
    def to_epub_extractor_format(book: BookIntermediate) -> Dict[str, Any]:
        """
        Convert intermediate representation to epub_extractor book_info.json format.
        """
        chapters_data = []
        
        for chapter in book.chapters:
            # Combine all text content from sections
            content_parts = []
            for section in chapter.sections:
                if section.type == "chapter_header":
                    continue  # Skip chapter header as it's already in title
                elif section.content:
                    content_parts.append(section.content)
            
            chapter_data = {
                "number": chapter.number,
                "title": chapter.title,
                "filename": chapter.filename or f"{chapter.number:02d}_{chapter.title.replace(' ', '_')}.txt",
                "content": "\n\n".join(content_parts)
            }
            chapters_data.append(chapter_data)
        
        return {
            "metadata": {
                "title": book.metadata.title,
                "author": book.metadata.author,
                "language": book.metadata.language,
                "identifier": book.metadata.identifier
            },
            "chapters": chapters_data,
            "total_chapters": len(chapters_data)
        }
