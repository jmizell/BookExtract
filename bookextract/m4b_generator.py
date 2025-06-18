"""
M4B Audiobook Generator - Core functionality for generating M4B audiobooks from intermediate format.

This module provides the core M4B generation functionality independent of any GUI framework.
It can be used programmatically or integrated with different user interfaces.
"""

import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from bookextract.book_intermediate import BookIntermediate
from bookextract.intermediate_to_m4b import process_intermediate_file_object, clean_text_for_tts


@dataclass
class M4bConfig:
    """Configuration for M4B generation."""
    tts_model: str = "am_michael"
    tts_language: str = "a"
    audio_bitrate: str = "64k"
    sample_rate: str = "22050"


class M4bGenerator:
    """
    Core M4B audiobook generator.
    
    This class handles the generation of M4B audiobooks from intermediate book format,
    including TTS processing, audio encoding, and metadata creation.
    """
    
    def __init__(self, config: Optional[M4bConfig] = None):
        """
        Initialize the M4B generator.
        
        Args:
            config: M4B generation configuration. If None, uses default config.
        """
        self.config = config or M4bConfig()
        self.temp_dir: Optional[Path] = None
        self.audio_dir: Optional[Path] = None
        
        # Callback functions for progress and logging
        self.progress_callback: Optional[Callable[[str], None]] = None
        self.log_callback: Optional[Callable[[str, str], None]] = None
        
    def set_progress_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback function for progress updates."""
        self.progress_callback = callback
        
    def set_log_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set callback function for log messages. Callback receives (message, level)."""
        self.log_callback = callback
        
    def _update_progress(self, message: str) -> None:
        """Update progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(message)
            
    def _log_message(self, message: str, level: str = "INFO") -> None:
        """Log message if callback is set."""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            # Fallback to print if no callback
            print(f"[{level}] {message}")
            
    def check_dependencies(self) -> Dict[str, bool]:
        """
        Check if required dependencies are available.
        
        Returns:
            Dictionary mapping dependency names to availability status.
        """
        self._log_message("Checking dependencies...")
        
        dependencies = {
            "python3": "Python 3 interpreter",
            "kokoro": "Kokoro TTS engine",
            "ffmpeg": "FFmpeg audio processing",
            "ffprobe": "FFprobe media analysis"
        }
        
        results = {}
        missing = []
        
        for cmd, desc in dependencies.items():
            try:
                result = subprocess.run([cmd, "--help"],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self._log_message(f"✓ {desc} found")
                    results[cmd] = True
                else:
                    missing.append(desc)
                    self._log_message(f"✗ {desc} not found", "WARNING")
                    results[cmd] = False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing.append(desc)
                self._log_message(f"✗ {desc} not found", "WARNING")
                results[cmd] = False
        
        if missing:
            self._log_message(f"Missing dependencies: {', '.join(missing)}", "ERROR")
        else:
            self._log_message("All dependencies found!", "SUCCESS")
            
        return results
        
    def generate_m4b(self, intermediate_data: BookIntermediate, output_path: str) -> None:
        """
        Generate M4B audiobook from intermediate data.
        
        Args:
            intermediate_data: BookIntermediate object containing book data
            output_path: Path where the M4B file should be saved
            
        Raises:
            Exception: If generation fails at any step
        """
        try:
            self._log_message("Starting M4B audiobook generation...")
            
            # Create temporary directories
            self.temp_dir = Path(tempfile.mkdtemp(prefix="m4b_temp_"))
            self.audio_dir = Path(tempfile.mkdtemp(prefix="audio_temp_"))
            
            self._log_message(f"Created temporary directories: {self.temp_dir}, {self.audio_dir}")
            
            # Step 1: Process intermediate format to create text files
            self._update_progress("Processing intermediate format...")
            self._log_message("Processing intermediate format...")
            
            process_intermediate_file_object(intermediate_data, self.temp_dir)
            
            # Step 2: Generate audio files using TTS
            self._update_progress("Generating audio files...")
            self._log_message("Generating audio files using Kokoro TTS...")
            
            self._generate_audio_files()
            
            # Step 3: Create M4B audiobook
            self._update_progress("Creating M4B audiobook...")
            self._log_message("Creating M4B audiobook...")
            
            self._create_m4b_audiobook(intermediate_data, output_path)
            
            # Success
            self._update_progress("M4B generation completed!")
            self._log_message(f"M4B audiobook created successfully: {output_path}", "SUCCESS")
            
            # Show file info
            self._show_audiobook_info(output_path)
            
        except Exception as e:
            error_msg = f"M4B generation error: {str(e)}"
            self._log_message(error_msg, "ERROR")
            raise
        finally:
            # Cleanup
            self._cleanup_temp_files()
            
    def _generate_audio_files(self) -> None:
        """Generate audio files using Kokoro TTS."""
        # Get list of text files in order
        text_files = sorted(self.temp_dir.glob("*.txt"))
        total_files = len(text_files)
        
        self._log_message(f"Found {total_files} text files to process")
        
        for i, txt_file in enumerate(text_files, 1):
            basename = txt_file.stem
            wav_file = self.audio_dir / f"{basename}.wav"
            
            self._log_message(f"Processing ({i}/{total_files}): {basename}")
            self._update_progress(f"Generating audio ({i}/{total_files}): {basename}")
            
            # Check if text file has content
            if txt_file.stat().st_size == 0:
                self._log_message(f"Skipping empty text file: {basename}", "WARNING")
                continue
            
            # Generate audio using Kokoro TTS
            cmd = [
                "kokoro",
                "-m", self.config.tts_model,
                "-l", self.config.tts_language,
                "-i", str(txt_file),
                "-o", str(wav_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Kokoro TTS failed for {basename}: {result.stderr}")
            
            # Verify audio file was created
            if not wav_file.exists():
                raise Exception(f"Audio file not created: {wav_file}")
                
        self._log_message("Audio generation completed")
        
    def _create_m4b_audiobook(self, intermediate_data: BookIntermediate, output_path: str) -> None:
        """Create M4B audiobook from audio files."""
        # Get book metadata
        metadata = intermediate_data.metadata
        
        # Create file list for ffmpeg
        audio_files = sorted(self.audio_dir.glob("*.wav"))
        if not audio_files:
            raise Exception("No audio files found")
            
        filelist_path = self.audio_dir / "filelist.txt"
        with open(filelist_path, 'w') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file.name}'\n")
        
        # Create chapter metadata
        metadata_path = self.audio_dir / "metadata.txt"
        self._create_chapter_metadata(intermediate_data, metadata_path, audio_files)
        
        # Combine all audio files and create M4B with metadata and chapters
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(filelist_path),
            "-i", str(metadata_path),
            "-map_metadata", "1",
            "-c:a", "aac",
            "-b:a", self.config.audio_bitrate,
            "-ar", self.config.sample_rate,
            "-movflags", "+faststart",
            "-metadata", f"title={metadata.title}",
            "-metadata", f"artist={metadata.author}",
            "-metadata", f"album={metadata.title}",
            "-metadata", "genre=Audiobook",
            "-metadata", "comment=Generated using M4B Audiobook Generator",
            "-y", str(output_path)
        ]
        
        # Change to audio directory for relative paths
        result = subprocess.run(cmd, cwd=self.audio_dir, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        if not Path(output_path).exists():
            raise Exception("M4B file was not created")
            
    def _create_chapter_metadata(self, intermediate_data: BookIntermediate, 
                                metadata_path: Path, audio_files: list) -> None:
        """Create chapter metadata for ffmpeg."""
        metadata = intermediate_data.metadata
        
        with open(metadata_path, 'w') as f:
            # Write metadata header
            f.write(";FFMETADATA1\n")
            f.write(f"title={metadata.title}\n")
            f.write(f"artist={metadata.author}\n")
            f.write(f"album={metadata.title}\n")
            f.write("genre=Audiobook\n")
            f.write("comment=Generated using M4B Audiobook Generator\n\n")
            
            # Calculate chapter start times
            current_time = 0
            
            for audio_file in audio_files:
                basename = audio_file.stem
                
                # Get duration of current audio file in milliseconds
                cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", 
                      "-of", "csv=p=0", str(audio_file)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Failed to get duration for {audio_file}")
                
                duration_seconds = float(result.stdout.strip())
                duration_ms = int(duration_seconds * 1000)
                
                # Determine chapter title
                if basename == "00_title":
                    chapter_title = "Title Page"
                else:
                    # Try to get chapter title from the intermediate data
                    try:
                        chapter_num = int(basename.split('_')[0])
                        chapter = next((ch for ch in intermediate_data.chapters 
                                      if ch.number == chapter_num), None)
                        if chapter:
                            chapter_title = f"Chapter {chapter.number}: {chapter.title}"
                        else:
                            chapter_title = f"Chapter {chapter_num}"
                    except (ValueError, IndexError):
                        chapter_title = basename.replace('_', ' ').title()
                
                # Write chapter metadata
                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={current_time}\n")
                f.write(f"END={current_time + duration_ms}\n")
                f.write(f"title={chapter_title}\n\n")
                
                current_time += duration_ms
                
    def _show_audiobook_info(self, m4b_path: str) -> None:
        """Show information about the generated audiobook."""
        try:
            # Get file size
            file_size = Path(m4b_path).stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # Get duration
            cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", 
                  "-of", "csv=p=0", str(m4b_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                duration_seconds = float(result.stdout.strip())
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                seconds = int(duration_seconds % 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = "Unknown"
            
            self._log_message("Audiobook Information:")
            self._log_message("=" * 30)
            self._log_message(f"File size: {file_size_mb:.1f} MB")
            self._log_message(f"Duration: {duration_str}")
            self._log_message(f"Output file: {m4b_path}")
            self._log_message("=" * 30)
            
        except Exception as e:
            self._log_message(f"Could not get audiobook info: {str(e)}", "WARNING")
            
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files and directories."""
        try:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self._log_message(f"Cleaned up temporary directory: {self.temp_dir}")
            if self.audio_dir and self.audio_dir.exists():
                shutil.rmtree(self.audio_dir)
                self._log_message(f"Cleaned up audio directory: {self.audio_dir}")
        except Exception as e:
            self._log_message(f"Error cleaning up temporary files: {str(e)}", "WARNING")
        finally:
            self.temp_dir = None
            self.audio_dir = None