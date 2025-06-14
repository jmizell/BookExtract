#!/usr/bin/env python3
"""
Intermediate to M4B Converter

This script converts book intermediate representation to text files suitable for TTS processing
and M4B audiobook generation. It can work with either the intermediate format or the legacy
book_info.json format.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from book_intermediate import BookIntermediate, BookConverter


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


def process_legacy_format(input_file: Path, output_dir: Path) -> None:
    """
    Process a legacy book_info.json file (for backward compatibility).
    
    Args:
        input_file: Path to book_info.json file
        output_dir: Directory to save output files
    """
    print(f"Processing legacy format file: {input_file}")
    
    # Convert to intermediate format first
    intermediate = BookConverter.from_epub_extractor(input_file)
    
    print(f"Converted to intermediate format: {intermediate.metadata.title} by {intermediate.metadata.author}")
    
    # Process as intermediate
    process_intermediate_file_object(intermediate, output_dir)


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


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Convert intermediate representation to M4B-ready text files')
    parser.add_argument('input_file', help='Path to intermediate JSON file or book_info.json')
    parser.add_argument('-o', '--output', default='m4b_ready', 
                       help='Output directory for text files')
    parser.add_argument('--format', choices=['auto', 'intermediate', 'legacy'], default='auto',
                       help='Input file format (auto-detect by default)')
    
    args = parser.parse_args()
    
    input_file = Path(args.input_file)
    output_dir = Path(args.output)
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Determine file format
        if args.format == 'auto':
            # Try to auto-detect format
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'format_version' in data or 'metadata' in data and 'chapters' in data and isinstance(data['chapters'], list) and len(data['chapters']) > 0 and 'sections' in data['chapters'][0]:
                file_format = 'intermediate'
            elif 'metadata' in data and 'chapters' in data and 'total_chapters' in data:
                file_format = 'legacy'
            else:
                print("Warning: Could not auto-detect format, assuming intermediate", file=sys.stderr)
                file_format = 'intermediate'
        else:
            file_format = args.format
        
        print(f"Detected format: {file_format}")
        
        # Process based on format
        if file_format == 'intermediate':
            process_intermediate_file(input_file, output_dir)
        elif file_format == 'legacy':
            process_legacy_format(input_file, output_dir)
        else:
            raise ValueError(f"Unknown format: {file_format}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()