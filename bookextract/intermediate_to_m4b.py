import json
from pathlib import Path
from bookextract import BookIntermediate, BookConverter


def create_text_files_from_intermediate(intermediate: BookIntermediate, output_dir: Path) -> None:
    """
    Create individual text files for each chapter from intermediate representation.
    Optimized for TTS processing with proper formatting and content handling.
    
    Args:
        intermediate: BookIntermediate object
        output_dir: Directory to save text files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create title page
    title_content = f"{intermediate.metadata.title}\n\nBy {intermediate.metadata.author}\n\n"
    title_file = output_dir / "00_title.txt"
    with open(title_file, 'w', encoding='utf-8') as f:
        f.write(title_content)
    
    print(f"Created title file: {title_file}")
    
    # Create chapter files
    for chapter in intermediate.chapters:
        # Generate filename
        safe_title = "".join(c for c in chapter.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        filename = f"{chapter.number:02d}_{safe_title}.txt"
        
        # Combine chapter content with TTS-optimized formatting
        content_parts = []
        
        # Add chapter title with proper spacing for TTS
        content_parts.append(f"Chapter {chapter.number}: {chapter.title}")
        content_parts.append("")  # Blank line after title
        
        for section in chapter.sections:
            if section.type == "chapter_header":
                continue  # Skip as we already have the title
            elif section.type == "paragraph":
                if section.content:
                    # Clean up paragraph content for TTS
                    cleaned_content = clean_text_for_tts(section.content)
                    content_parts.append(cleaned_content)
            elif section.type in ["header", "sub_header"]:
                if section.content:
                    # Headers get extra spacing and formatting for TTS
                    cleaned_content = clean_text_for_tts(section.content)
                    content_parts.append(f"\n{cleaned_content}\n")
            elif section.type == "bold":
                if section.content:
                    # Bold text is emphasized in TTS
                    cleaned_content = clean_text_for_tts(section.content)
                    content_parts.append(cleaned_content)
            elif section.type == "block_indent":
                if section.content:
                    # Block quotes get special formatting
                    cleaned_content = clean_text_for_tts(section.content)
                    content_parts.append(f"\n{cleaned_content}\n")
            elif section.type == "page_division":
                # Page breaks become pauses in TTS
                content_parts.append("\n")
            elif section.type == "image":
                # Handle image descriptions for TTS
                if section.caption:
                    content_parts.append(f"[Image: {section.caption}]")
                elif section.content:
                    content_parts.append(f"[Image: {section.content}]")
            elif section.content:
                # Any other content type
                cleaned_content = clean_text_for_tts(section.content)
                content_parts.append(cleaned_content)
        
        # Write chapter file with proper spacing
        chapter_file = output_dir / filename
        chapter_content = "\n\n".join(filter(None, content_parts))
        
        # Ensure content is not empty
        if not chapter_content.strip():
            chapter_content = f"Chapter {chapter.number}: {chapter.title}\n\nThis chapter appears to be empty."
        
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(chapter_content)
        
        word_count = len(chapter_content.split())
        print(f"Created chapter file: {chapter_file} ({word_count} words)")


def clean_text_for_tts(text: str) -> str:
    """
    Clean and optimize text content for TTS processing.
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text optimized for TTS
    """
    if not text:
        return ""
    
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Fix common punctuation issues for better TTS pronunciation
    text = re.sub(r'\.{2,}', '...', text)  # Normalize ellipses
    text = re.sub(r'--+', ' -- ', text)    # Normalize multiple dashes
    # Don't normalize single dashes as they might be hyphens in words
    
    # Ensure proper sentence endings
    text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
    
    # Remove or replace problematic characters for TTS
    text = text.replace('"', '"').replace('"', '"')  # Smart quotes to regular quotes
    text = text.replace(''', "'").replace(''', "'")  # Smart apostrophes
    text = text.replace('…', '...')  # Ellipsis character to dots
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    # Ensure text ends with proper punctuation for TTS
    if text and not text[-1] in '.!?':
        text += '.'
    
    return text


def create_metadata_file(intermediate: BookIntermediate, output_dir: Path) -> None:
    """
    Create a metadata file compatible with the M4B pipeline.
    
    Args:
        intermediate: BookIntermediate object
        output_dir: Directory to save metadata file
    """
    # Convert to legacy format for compatibility
    legacy_format = BookConverter.to_epub_extractor_format(intermediate)
    
    metadata_file = output_dir / "book_info.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(legacy_format, f, indent=2, ensure_ascii=False)
    
    print(f"Created metadata file: {metadata_file}")


def process_intermediate_file(input_file: Path, output_dir: Path) -> None:
    """
    Process an intermediate representation file for M4B generation.
    
    Args:
        input_file: Path to intermediate JSON file
        output_dir: Directory to save output files
    """
    print(f"Processing intermediate file: {input_file}")
    
    # Load intermediate representation
    intermediate = BookIntermediate.load_from_file(input_file)
    
    print(f"Loaded book: {intermediate.metadata.title} by {intermediate.metadata.author}")
    print(f"Chapters: {intermediate.get_chapter_count()}")
    print(f"Total words: {intermediate.get_total_word_count()}")
    
    # Create text files for TTS
    create_text_files_from_intermediate(intermediate, output_dir)
    
    # Create metadata file for compatibility
    create_metadata_file(intermediate, output_dir)
    
    print(f"\nProcessing complete! Files saved to: {output_dir}")

def process_intermediate_file_object(intermediate: BookIntermediate, output_dir: Path) -> None:
    """
    Process an intermediate representation object for M4B generation.
    
    Args:
        intermediate: BookIntermediate object
        output_dir: Directory to save output files
    """
    print(f"Processing book: {intermediate.metadata.title} by {intermediate.metadata.author}")
    print(f"Chapters: {intermediate.get_chapter_count()}")
    print(f"Total words: {intermediate.get_total_word_count()}")
    
    # Create text files for TTS
    create_text_files_from_intermediate(intermediate, output_dir)
    
    # Create metadata file for compatibility
    create_metadata_file(intermediate, output_dir)
    
    print(f"\nProcessing complete! Files saved to: {output_dir}")
