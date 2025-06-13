#!/bin/bash

# EPUB to M4B Audiobook Converter
# Converts EPUB files to M4B audiobooks with metadata and chapter markers
# 
# Usage: ./epub_to_m4b.sh <epub_file> [output_name]
#
# Requirements:
# - Python 3 with ebooklib, beautifulsoup4
# - Kokoro TTS (for audio generation)
# - ffmpeg (for audio processing and M4B creation)

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="epub_temp_$$"
AUDIO_DIR="audio_temp_$$"
TTS_MODEL="am_michael"  # Kokoro TTS model
TTS_LANG="a"           # Kokoro language setting
AUDIO_BITRATE="64k"    # Audio bitrate for M4B
SAMPLE_RATE="22050"    # Sample rate for audio

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup temporary files
cleanup() {
    print_status "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR" "$AUDIO_DIR" 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python and required modules
    if ! python3 -c "import ebooklib, bs4" 2>/dev/null; then
        print_error "Missing Python dependencies. Please install: pip install EbookLib beautifulsoup4"
        exit 1
    fi
    
    # Check Kokoro TTS
    if ! command -v kokoro &> /dev/null; then
        print_error "Kokoro TTS not found. Please install kokoro."
        exit 1
    fi
    
    # Check ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        print_error "ffmpeg not found. Please install ffmpeg."
        exit 1
    fi
    
    print_success "All dependencies found"
}

# Function to extract text from EPUB
extract_epub() {
    local epub_file="$1"
    
    print_status "Extracting text from EPUB: $(basename "$epub_file")"
    
    python3 "$SCRIPT_DIR/epub_extractor.py" "$epub_file" -o "$TEMP_DIR"
    
    if [ ! -f "$TEMP_DIR/book_info.json" ]; then
        print_error "Failed to extract EPUB content"
        exit 1
    fi
    
    print_success "EPUB extraction completed"
}

# Function to generate audio files using TTS
generate_audio() {
    print_status "Generating audio files using Kokoro TTS..."
    
    mkdir -p "$AUDIO_DIR"
    
    # Get list of text files in order
    local text_files=($(ls "$TEMP_DIR"/*.txt | sort))
    local total_files=${#text_files[@]}
    local current=0
    
    for txt_file in "${text_files[@]}"; do
        current=$((current + 1))
        local basename=$(basename "$txt_file" .txt)
        local wav_file="$AUDIO_DIR/${basename}.wav"
        
        print_status "Processing ($current/$total_files): $basename"
        
        # Generate audio using Kokoro TTS
        if ! kokoro -m "$TTS_MODEL" -l "$TTS_LANG" -i "$txt_file" -o "$wav_file"; then
            print_error "Failed to generate audio for $basename"
            exit 1
        fi
        
        # Verify audio file was created
        if [ ! -f "$wav_file" ]; then
            print_error "Audio file not created: $wav_file"
            exit 1
        fi
    done
    
    print_success "Audio generation completed"
}

# Function to create chapter metadata for ffmpeg
create_chapter_metadata() {
    local metadata_file="$1"
    local book_info_file="$TEMP_DIR/book_info.json"
    
    print_status "Creating chapter metadata..."
    
    # Start with metadata file header
    cat > "$metadata_file" << EOF
;FFMETADATA1
title=$(python3 -c "import json; data=json.load(open('$book_info_file')); print(data['metadata']['title'])")
artist=$(python3 -c "import json; data=json.load(open('$book_info_file')); print(data['metadata']['author'])")
album=$(python3 -c "import json; data=json.load(open('$book_info_file')); print(data['metadata']['title'])")
genre=Audiobook
comment=Generated from EPUB using epub_to_m4b.sh

EOF

    # Get audio files in order and calculate chapter start times
    local audio_files=($(ls "$AUDIO_DIR"/*.wav | sort))
    local current_time=0
    local chapter_num=0
    
    for audio_file in "${audio_files[@]}"; do
        local basename=$(basename "$audio_file" .wav)
        
        # Get duration of current audio file in milliseconds
        local duration_ms=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$audio_file" | awk '{print int($1 * 1000)}')
        
        # Determine chapter title
        local chapter_title
        if [[ "$basename" == "00_title" ]]; then
            chapter_title="Title Page"
        else
            # Extract chapter title from the text file
            chapter_title=$(head -n 1 "$TEMP_DIR/${basename}.txt" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            if [ -z "$chapter_title" ]; then
                chapter_title="Chapter $((chapter_num + 1))"
            fi
        fi
        
        # Add chapter metadata
        cat >> "$metadata_file" << EOF
[CHAPTER]
TIMEBASE=1/1000
START=$current_time
END=$((current_time + duration_ms))
title=$chapter_title

EOF
        
        current_time=$((current_time + duration_ms))
        chapter_num=$((chapter_num + 1))
    done
    
    print_success "Chapter metadata created"
}

# Function to combine audio files and create M4B
create_m4b() {
    local output_file="$1"
    local book_info_file="$TEMP_DIR/book_info.json"
    
    print_status "Creating M4B audiobook..."
    
    # Get book metadata
    local title=$(python3 -c "import json; data=json.load(open('$book_info_file')); print(data['metadata']['title'])")
    local author=$(python3 -c "import json; data=json.load(open('$book_info_file')); print(data['metadata']['author'])")
    
    # Create file list for ffmpeg
    local filelist="$AUDIO_DIR/filelist.txt"
    (cd "$AUDIO_DIR" && ls *.wav | sort | sed "s|^|file '|" | sed "s|$|'|") > "$filelist"
    
    # Create chapter metadata
    local metadata_file="$AUDIO_DIR/metadata.txt"
    create_chapter_metadata "$metadata_file"
    
    # Combine all audio files and create M4B with metadata and chapters
    print_status "Combining audio files and adding metadata..."
    
    ffmpeg -f concat -safe 0 -i "$filelist" \
           -i "$metadata_file" \
           -map_metadata 1 \
           -c:a aac \
           -b:a "$AUDIO_BITRATE" \
           -ar "$SAMPLE_RATE" \
           -movflags +faststart \
           -metadata title="$title" \
           -metadata artist="$author" \
           -metadata album="$title" \
           -metadata genre="Audiobook" \
           -metadata comment="Generated from EPUB using epub_to_m4b.sh" \
           -y "$output_file"
    
    if [ ! -f "$output_file" ]; then
        print_error "Failed to create M4B file"
        exit 1
    fi
    
    print_success "M4B audiobook created: $output_file"
}

# Function to display file information
show_info() {
    local m4b_file="$1"
    local book_info_file="$TEMP_DIR/book_info.json"
    
    print_status "Audiobook Information:"
    echo "=========================="
    
    # Get metadata from JSON
    local title=$(python3 -c "import json; data=json.load(open('$book_info_file')); print(data['metadata']['title'])")
    local author=$(python3 -c "import json; data=json.load(open('$book_info_file')); print(data['metadata']['author'])")
    local chapters=$(python3 -c "import json; data=json.load(open('$book_info_file')); print(data['total_chapters'])")
    
    echo "Title: $title"
    echo "Author: $author"
    echo "Chapters: $chapters"
    
    # Get file size and duration
    local file_size=$(du -h "$m4b_file" | cut -f1)
    local duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$m4b_file" | awk '{printf "%02d:%02d:%02d", $1/3600, ($1%3600)/60, $1%60}')
    
    echo "File size: $file_size"
    echo "Duration: $duration"
    echo "Output file: $m4b_file"
    echo "=========================="
}

# Main function
main() {
    local epub_file="$1"
    local output_name="$2"
    
    # Validate input
    if [ -z "$epub_file" ]; then
        echo "Usage: $0 <epub_file> [output_name]"
        echo ""
        echo "Convert EPUB to M4B audiobook with metadata and chapter markers"
        echo ""
        echo "Arguments:"
        echo "  epub_file    Path to the EPUB file to convert"
        echo "  output_name  Optional output filename (without extension)"
        echo ""
        echo "Example:"
        echo "  $0 mybook.epub"
        echo "  $0 mybook.epub \"My Custom Audiobook\""
        exit 1
    fi
    
    if [ ! -f "$epub_file" ]; then
        print_error "EPUB file not found: $epub_file"
        exit 1
    fi
    
    # Determine output filename
    if [ -z "$output_name" ]; then
        output_name=$(basename "$epub_file" .epub)
    fi
    local m4b_file="${output_name}.m4b"
    
    print_status "Starting EPUB to M4B conversion"
    print_status "Input: $epub_file"
    print_status "Output: $m4b_file"
    echo ""
    
    # Check dependencies
    check_dependencies
    echo ""
    
    # Extract EPUB content
    extract_epub "$epub_file"
    echo ""
    
    # Generate audio files
    generate_audio
    echo ""
    
    # Create M4B audiobook
    create_m4b "$m4b_file"
    echo ""
    
    # Show information
    show_info "$m4b_file"
    echo ""
    
    print_success "Conversion completed successfully!"
    print_status "Your audiobook is ready: $m4b_file"
}

# Run main function with all arguments
main "$@"