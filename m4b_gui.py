#!/usr/bin/env python3
"""
M4B Audiobook Generator GUI - A tkinter interface for M4B audiobook generation from intermediate format.

This application provides a user-friendly interface to load intermediate format files
and generate M4B audiobooks with TTS, metadata, and chapter markers.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import tempfile
import threading
import subprocess
import shutil
from pathlib import Path
import uuid
from book_intermediate import BookIntermediate, BookConverter
from intermediate_to_m4b import process_intermediate_file_object, clean_text_for_tts


class M4bGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("M4B Audiobook Generator")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # State variables
        self.current_intermediate_file = None
        self.current_intermediate_data = None
        self.is_generating = False
        self.generation_thread = None
        self.temp_dir = None
        self.audio_dir = None
        
        # Default values
        self.default_input_folder = str(Path.cwd() / "out")
        self.default_output_folder = str(Path.cwd() / "out")
        
        # TTS Configuration
        self.tts_model = tk.StringVar(value="am_michael")
        self.tts_language = tk.StringVar(value="a")
        self.audio_bitrate = tk.StringVar(value="64k")
        self.sample_rate = tk.StringVar(value="22050")
        self.output_filename = tk.StringVar()
        
        self.setup_ui()
        self.check_dependencies()
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
        file_menu.add_command(label="Generate M4B...", command=self.generate_m4b, accelerator="Ctrl+G")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Check Dependencies", command=self.check_dependencies)
        tools_menu.add_command(label="Clear Log", command=self.clear_log)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="TTS Models Help", command=self.show_tts_help)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_intermediate())
        self.root.bind('<Control-g>', lambda e: self.generate_m4b())
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
        
        # Left panel - Book Information and Settings
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # Book Information Section
        book_frame = ttk.LabelFrame(left_frame, text="Book Information", padding="5")
        book_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        book_frame.columnconfigure(0, weight=1)
        
        # File toolbar
        file_toolbar = ttk.Frame(book_frame)
        file_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(file_toolbar, text="Open Intermediate", command=self.open_intermediate).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(file_toolbar, text="Generate M4B", command=self.generate_m4b).pack(side=tk.LEFT, padx=(0, 2))
        
        # Book metadata display
        metadata_frame = ttk.Frame(book_frame)
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
        
        # TTS Configuration Section
        config_frame = ttk.LabelFrame(left_frame, text="TTS Configuration", padding="5")
        config_frame.grid(row=1, column=0, sticky="nsew")
        config_frame.columnconfigure(1, weight=1)
        
        # TTS Model
        ttk.Label(config_frame, text="TTS Model:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        model_combo = ttk.Combobox(config_frame, textvariable=self.tts_model, 
                                  values=["am_michael", "am_adam", "am_domi", "af_bella", "af_sarah", "af_nicole"])
        model_combo.grid(row=0, column=1, sticky="ew", pady=2)
        
        # TTS Language
        ttk.Label(config_frame, text="Language:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        lang_combo = ttk.Combobox(config_frame, textvariable=self.tts_language,
                                 values=["a", "b", "c"])
        lang_combo.grid(row=1, column=1, sticky="ew", pady=2)
        
        # Audio Bitrate
        ttk.Label(config_frame, text="Audio Bitrate:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=2)
        bitrate_combo = ttk.Combobox(config_frame, textvariable=self.audio_bitrate,
                                    values=["32k", "64k", "96k", "128k", "192k"])
        bitrate_combo.grid(row=2, column=1, sticky="ew", pady=2)
        
        # Sample Rate
        ttk.Label(config_frame, text="Sample Rate:").grid(row=3, column=0, sticky="w", padx=(0, 5), pady=2)
        rate_combo = ttk.Combobox(config_frame, textvariable=self.sample_rate,
                                 values=["16000", "22050", "44100", "48000"])
        rate_combo.grid(row=3, column=1, sticky="ew", pady=2)
        
        # Output filename
        ttk.Label(config_frame, text="Output Name:").grid(row=4, column=0, sticky="w", padx=(0, 5), pady=2)
        ttk.Entry(config_frame, textvariable=self.output_filename).grid(row=4, column=1, sticky="ew", pady=2)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(left_frame, text="Progress", padding="5")
        progress_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky="w")
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # Right panel - Chapter List and Preview
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Chapter list
        chapters_frame = ttk.LabelFrame(right_frame, text="Chapters", padding="5")
        chapters_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 2))
        chapters_frame.columnconfigure(0, weight=1)
        chapters_frame.rowconfigure(0, weight=1)
        
        # Chapter listbox with scrollbar
        list_frame = ttk.Frame(chapters_frame)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.chapters_listbox = tk.Listbox(list_frame, font=("Arial", 9))
        self.chapters_listbox.grid(row=0, column=0, sticky="nsew")
        self.chapters_listbox.bind('<<ListboxSelect>>', self.on_chapter_select)
        
        chapters_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.chapters_listbox.yview)
        chapters_scrollbar.grid(row=0, column=1, sticky="ns")
        self.chapters_listbox.configure(yscrollcommand=chapters_scrollbar.set)
        
        # Preview area
        preview_frame = ttk.LabelFrame(right_frame, text="Chapter Preview", padding="5")
        preview_frame.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_area = scrolledtext.ScrolledText(
            preview_frame,
            wrap=tk.WORD,
            font=("Georgia", 10),
            state=tk.DISABLED
        )
        self.preview_area.grid(row=0, column=0, sticky="nsew")
        
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
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log console."""
        self.log_console.config(state=tk.NORMAL)
        self.log_console.delete(1.0, tk.END)
        self.log_console.config(state=tk.DISABLED)
        
    def check_dependencies(self):
        """Check if required dependencies are available."""
        self.log_message("Checking dependencies...")
        
        dependencies = {
            "python3": "Python 3 interpreter",
            "kokoro": "Kokoro TTS engine",
            "ffmpeg": "FFmpeg audio processing",
            "ffprobe": "FFprobe media analysis"
        }
        
        missing = []
        for cmd, desc in dependencies.items():
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log_message(f"✓ {desc} found")
                else:
                    missing.append(desc)
                    self.log_message(f"✗ {desc} not found", "WARNING")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing.append(desc)
                self.log_message(f"✗ {desc} not found", "WARNING")
        
        if missing:
            self.log_message(f"Missing dependencies: {', '.join(missing)}", "ERROR")
            messagebox.showwarning("Dependencies Missing", 
                                 f"The following dependencies are missing:\n\n" +
                                 "\n".join(f"• {dep}" for dep in missing) +
                                 "\n\nPlease install them before generating M4B files.")
        else:
            self.log_message("All dependencies found!", "SUCCESS")
            
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
                
                # Set default output filename
                if not self.output_filename.get():
                    clean_title = "".join(c for c in intermediate.metadata.title 
                                        if c.isalnum() or c in (' ', '-', '_')).strip()
                    clean_title = clean_title.replace(' ', '_')
                    self.output_filename.set(clean_title)
                
                self.log_message(f"Opened intermediate file: {file_path}")
                self.log_message(f"Loaded {intermediate.get_chapter_count()} chapters, {intermediate.get_total_word_count()} words")
                
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
            
    def on_chapter_select(self, event):
        """Handle chapter selection in the listbox."""
        selection = self.chapters_listbox.curselection()
        if selection and self.current_intermediate_data:
            chapter_index = selection[0]
            chapter = self.current_intermediate_data.chapters[chapter_index]
            self.update_chapter_preview(chapter)
            
    def update_chapter_preview(self, chapter):
        """Update the chapter preview area."""
        self.preview_area.config(state=tk.NORMAL)
        self.preview_area.delete(1.0, tk.END)
        
        # Show chapter title
        self.preview_area.insert(tk.END, f"Chapter {chapter.number}: {chapter.title}\n")
        self.preview_area.insert(tk.END, "=" * 50 + "\n\n")
        
        # Show processed content (as it would appear for TTS)
        content_parts = []
        for section in chapter.sections:
            if section.type == "chapter_header":
                continue  # Skip as we already have the title
            elif section.type == "paragraph" and section.content:
                cleaned_content = clean_text_for_tts(section.content)
                content_parts.append(cleaned_content)
            elif section.type in ["header", "sub_header"] and section.content:
                cleaned_content = clean_text_for_tts(section.content)
                content_parts.append(f"\n{cleaned_content}\n")
            elif section.content:
                cleaned_content = clean_text_for_tts(section.content)
                content_parts.append(cleaned_content)
        
        chapter_content = "\n\n".join(filter(None, content_parts))
        if not chapter_content.strip():
            chapter_content = "This chapter appears to be empty."
            
        self.preview_area.insert(tk.END, chapter_content)
        self.preview_area.config(state=tk.DISABLED)
        
    def generate_m4b(self):
        """Generate M4B audiobook from the current intermediate data."""
        if not self.current_intermediate_data:
            messagebox.showwarning("Warning", "No intermediate data loaded")
            return
            
        if self.is_generating:
            messagebox.showinfo("Info", "M4B generation is already in progress")
            return
            
        # Get output filename
        output_name = self.output_filename.get().strip()
        if not output_name:
            messagebox.showwarning("Warning", "Please specify an output filename")
            return
            
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            title="Save M4B Audiobook",
            initialdir=self.default_output_folder,
            initialfile=f"{output_name}.m4b",
            defaultextension=".m4b",
            filetypes=[("M4B files", "*.m4b"), ("All files", "*.*")]
        )
        
        if file_path:
            self.is_generating = True
            self.progress_var.set("Starting M4B generation...")
            self.progress_bar.start()
            
            # Start generation in separate thread
            self.generation_thread = threading.Thread(
                target=self._generate_m4b_thread,
                args=(file_path,)
            )
            self.generation_thread.daemon = True
            self.generation_thread.start()
            
    def _generate_m4b_thread(self, output_path):
        """Generate M4B audiobook in a separate thread."""
        try:
            self.log_message("Starting M4B audiobook generation...")
            
            # Create temporary directories
            self.temp_dir = Path(tempfile.mkdtemp(prefix="m4b_temp_"))
            self.audio_dir = Path(tempfile.mkdtemp(prefix="audio_temp_"))
            
            self.log_message(f"Created temporary directories: {self.temp_dir}, {self.audio_dir}")
            
            # Step 1: Process intermediate format to create text files
            self.root.after(0, lambda: self.progress_var.set("Processing intermediate format..."))
            self.log_message("Processing intermediate format...")
            
            process_intermediate_file_object(self.current_intermediate_data, self.temp_dir)
            
            # Step 2: Generate audio files using TTS
            self.root.after(0, lambda: self.progress_var.set("Generating audio files..."))
            self.log_message("Generating audio files using Kokoro TTS...")
            
            self._generate_audio_files()
            
            # Step 3: Create M4B audiobook
            self.root.after(0, lambda: self.progress_var.set("Creating M4B audiobook..."))
            self.log_message("Creating M4B audiobook...")
            
            self._create_m4b_audiobook(output_path)
            
            # Success
            self.root.after(0, lambda: self.progress_var.set("M4B generation completed!"))
            self.log_message(f"M4B audiobook created successfully: {output_path}", "SUCCESS")
            
            # Show file info
            self._show_audiobook_info(output_path)
            
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                f"M4B audiobook generated successfully!\n\nOutput: {output_path}"))
            
        except Exception as e:
            error_msg = f"M4B generation error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.log_message(msg, "ERROR"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate M4B:\n{str(e)}"))
        finally:
            # Cleanup
            self._cleanup_temp_files()
            self.is_generating = False
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_var.set("Ready"))
            
    def _generate_audio_files(self):
        """Generate audio files using Kokoro TTS."""
        # Get list of text files in order
        text_files = sorted(self.temp_dir.glob("*.txt"))
        total_files = len(text_files)
        
        self.log_message(f"Found {total_files} text files to process")
        
        for i, txt_file in enumerate(text_files, 1):
            basename = txt_file.stem
            wav_file = self.audio_dir / f"{basename}.wav"
            
            self.log_message(f"Processing ({i}/{total_files}): {basename}")
            self.root.after(0, lambda b=basename, c=i, t=total_files: 
                          self.progress_var.set(f"Generating audio ({c}/{t}): {b}"))
            
            # Check if text file has content
            if txt_file.stat().st_size == 0:
                self.log_message(f"Skipping empty text file: {basename}", "WARNING")
                continue
            
            # Generate audio using Kokoro TTS
            cmd = [
                "kokoro",
                "-m", self.tts_model.get(),
                "-l", self.tts_language.get(),
                "-i", str(txt_file),
                "-o", str(wav_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Kokoro TTS failed for {basename}: {result.stderr}")
            
            # Verify audio file was created
            if not wav_file.exists():
                raise Exception(f"Audio file not created: {wav_file}")
                
        self.log_message("Audio generation completed")
        
    def _create_m4b_audiobook(self, output_path):
        """Create M4B audiobook from audio files."""
        # Get book metadata
        metadata = self.current_intermediate_data.metadata
        
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
        self._create_chapter_metadata(metadata_path, audio_files)
        
        # Combine all audio files and create M4B with metadata and chapters
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(filelist_path),
            "-i", str(metadata_path),
            "-map_metadata", "1",
            "-c:a", "aac",
            "-b:a", self.audio_bitrate.get(),
            "-ar", self.sample_rate.get(),
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
            
    def _create_chapter_metadata(self, metadata_path, audio_files):
        """Create chapter metadata for ffmpeg."""
        metadata = self.current_intermediate_data.metadata
        
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
                        chapter = next((ch for ch in self.current_intermediate_data.chapters 
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
                
    def _show_audiobook_info(self, m4b_path):
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
            
            metadata = self.current_intermediate_data.metadata
            
            self.log_message("Audiobook Information:")
            self.log_message("=" * 30)
            self.log_message(f"Title: {metadata.title}")
            self.log_message(f"Author: {metadata.author}")
            self.log_message(f"Chapters: {len(self.current_intermediate_data.chapters)}")
            self.log_message(f"File size: {file_size_mb:.1f} MB")
            self.log_message(f"Duration: {duration_str}")
            self.log_message(f"Output file: {m4b_path}")
            self.log_message("=" * 30)
            
        except Exception as e:
            self.log_message(f"Could not get audiobook info: {str(e)}", "WARNING")
            
    def _cleanup_temp_files(self):
        """Clean up temporary files and directories."""
        try:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.log_message(f"Cleaned up temporary directory: {self.temp_dir}")
            if self.audio_dir and self.audio_dir.exists():
                shutil.rmtree(self.audio_dir)
                self.log_message(f"Cleaned up audio directory: {self.audio_dir}")
        except Exception as e:
            self.log_message(f"Error cleaning up temporary files: {str(e)}", "WARNING")
        finally:
            self.temp_dir = None
            self.audio_dir = None
            
    def load_default_intermediate(self):
        """Try to load a default intermediate file if available."""
        default_path = Path(self.default_input_folder) / "book_intermediate.json"
        if default_path.exists():
            try:
                intermediate = BookIntermediate.load_from_file(default_path)
                self.current_intermediate_file = str(default_path)
                self.current_intermediate_data = intermediate
                self.update_metadata_display(intermediate)
                self.update_chapters_list(intermediate)
                self.log_message(f"Loaded default intermediate file: {default_path}")
            except Exception as e:
                self.log_message(f"Could not load default intermediate file: {str(e)}", "WARNING")
                
    def show_about(self):
        """Show about dialog."""
        about_text = """M4B Audiobook Generator

A GUI application for generating M4B audiobooks from intermediate book format.

Features:
• Load intermediate book format files
• Configure TTS settings (model, language, bitrate)
• Generate high-quality M4B audiobooks with chapters
• Progress tracking and detailed logging

Requirements:
• Python 3 with tkinter
• Kokoro TTS engine
• FFmpeg for audio processing

Version 1.0
"""
        messagebox.showinfo("About M4B Audiobook Generator", about_text)
        
    def show_tts_help(self):
        """Show TTS models help dialog."""
        help_text = """TTS Models and Settings

Available Kokoro TTS Models:
• am_michael - Male American English (default)
• am_adam - Male American English
• am_domi - Male American English
• af_bella - Female American English
• af_sarah - Female American English
• af_nicole - Female American English

Language Settings:
• a - Standard pronunciation
• b - Alternative pronunciation
• c - Expressive pronunciation

Audio Quality Settings:
• Bitrate: Higher values = better quality, larger files
• Sample Rate: 22050 Hz recommended for audiobooks

Recommended Settings:
• For general audiobooks: am_michael, language a, 64k bitrate
• For higher quality: 96k or 128k bitrate
• For smaller files: 32k bitrate
"""
        messagebox.showinfo("TTS Models Help", help_text)


def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    app = M4bGeneratorGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.is_generating:
            if messagebox.askokcancel("Quit", "M4B generation is in progress. Do you want to quit anyway?"):
                app._cleanup_temp_files()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()