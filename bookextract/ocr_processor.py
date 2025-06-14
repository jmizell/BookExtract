"""
OCR Processing Module

This module contains the core OCR and merge functionality separated from the GUI.
It handles basic OCR with tesseract, LLM cleanup, and content merging across pages.
"""

import subprocess
import json
import base64
import requests
import glob
import concurrent.futures
from pathlib import Path


class OCRProcessor:
    """
    Handles OCR processing, LLM cleanup, and content merging.
    
    This class is independent of the GUI and uses callbacks to report progress
    and log messages back to the calling interface.
    """
    
    def __init__(self, api_url="", api_token="", model="", max_workers=15):
        """
        Initialize the OCR processor.
        
        Args:
            api_url (str): API endpoint URL for LLM processing
            api_token (str): API authentication token
            model (str): Model name to use for LLM processing
            max_workers (int): Maximum number of concurrent workers for LLM processing
        """
        self.api_url = api_url
        self.api_token = api_token
        self.model = model
        self.max_workers = max_workers
        self.is_cancelled = False
        
        # Callbacks for progress reporting and logging
        self.progress_callback = None
        self.log_callback = None
        
    def set_callbacks(self, progress_callback=None, log_callback=None):
        """
        Set callback functions for progress reporting and logging.
        
        Args:
            progress_callback (callable): Function to call with progress updates
                Should accept (current_value, status_message)
            log_callback (callable): Function to call with log messages
                Should accept (message)
        """
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
    def cancel(self):
        """Cancel the current processing operation."""
        self.is_cancelled = True
        
    def _log(self, message):
        """Internal method to log a message via callback."""
        if self.log_callback:
            self.log_callback(message)
            
    def _update_progress(self, current, status):
        """Internal method to update progress via callback."""
        if self.progress_callback:
            self.progress_callback(current, status)
            
    def run_basic_ocr(self, input_folder, output_folder, total_files=None):
        """
        Run basic OCR using tesseract.
        
        Args:
            input_folder (Path): Directory containing input images
            output_folder (Path): Directory to save OCR text files
            total_files (int): Total number of files for progress calculation
            
        Returns:
            bool: True if successful, False if failed or cancelled
        """
        try:
            # Find all image files
            image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff']
            image_files = []
            for ext in image_extensions:
                image_files.extend(glob.glob(str(input_folder / ext)))
                image_files.extend(glob.glob(str(input_folder / ext.upper())))
            
            image_files.sort()
            processed_files = 0
            
            for i, image_path in enumerate(image_files):
                if self.is_cancelled:
                    return False
                    
                image_file = Path(image_path)
                output_name = image_file.stem
                txt_output = output_folder / f"{output_name}.txt"
                
                # Skip if already processed
                if txt_output.exists():
                    self._log(f"Skipping {image_file.name} (already processed)")
                    continue
                    
                self._log(f"Processing {image_file.name} with tesseract...")
                
                try:
                    # Run tesseract
                    result = subprocess.run([
                        'tesseract', str(image_path), str(output_folder / output_name)
                    ], capture_output=True, text=True, check=True)
                    
                    # Post-process the text file (same as ocr.sh)
                    if txt_output.exists():
                        with open(txt_output, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Apply the same sed transformations as in ocr.sh
                        # Replace double newlines with null, single newlines with space, null back to double newlines
                        content = content.replace('\n\n', '\x00')
                        content = content.replace('\n', ' ')
                        content = content.replace('\x00', '\n\n')
                        
                        with open(txt_output, 'w', encoding='utf-8') as f:
                            f.write(content)
                            
                        self._log(f"Wrote {txt_output}")
                        
                except subprocess.CalledProcessError as e:
                    self._log(f"Error processing {image_file.name}: {e}")
                    continue
                    
                # Update progress
                processed_files += 1
                if total_files:
                    progress_value = processed_files
                    self._update_progress(progress_value, f"Basic OCR: {processed_files}/{len(image_files)}")
                
            return True
            
        except Exception as e:
            self._log(f"Basic OCR error: {e}")
            return False
            
    def run_llm_cleanup(self, output_folder, total_files=None):
        """
        Run LLM cleanup on OCR results.
        
        Args:
            output_folder (Path): Directory containing text files to process
            total_files (int): Total number of files for progress calculation
            
        Returns:
            bool: True if successful, False if failed or cancelled
        """
        try:
            # Find all text files
            text_files = list(output_folder.glob("*.txt"))
            text_files.sort()
            
            if not text_files:
                self._log("No text files found for LLM cleanup")
                return True
                
            # Process files concurrently or sequentially
            if self.max_workers == 1:
                # Sequential processing for debugging
                completed = 0
                for txt_file in text_files:
                    if self.is_cancelled:
                        return False
                    
                    try:
                        result = self.process_single_file(txt_file)
                        if result:
                            completed += 1
                            if total_files:
                                progress_value = (total_files // 2) + (completed * (total_files // 2) // len(text_files))
                                self._update_progress(progress_value, f"LLM cleanup: {completed}/{len(text_files)}")
                            self._log(f"Completed LLM processing for {txt_file.name}")
                        else:
                            self._log(f"Failed LLM processing for {txt_file.name}")
                    except Exception as e:
                        self._log(f"Processing exception for {txt_file.name}: {e}")
            else:
                # Concurrent processing
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all tasks
                    futures = {executor.submit(self.process_single_file, txt_file): txt_file for txt_file in text_files}
                    
                    # Process results as they complete
                    completed = 0
                    for future in concurrent.futures.as_completed(futures):
                        if self.is_cancelled:
                            return False
                            
                        txt_file = futures[future]
                        try:
                            result = future.result()
                            if result:
                                completed += 1
                                if total_files:
                                    progress_value = (total_files // 2) + (completed * (total_files // 2) // len(text_files))
                                    self._update_progress(progress_value, f"LLM cleanup: {completed}/{len(text_files)}")
                                self._log(f"Completed LLM processing for {txt_file.name}")
                            else:
                                self._log(f"Failed LLM processing for {txt_file.name}")
                        except Exception as e:
                            self._log(f"Worker exception for {txt_file.name}: {e}")
                        
            return True
            
        except Exception as e:
            self._log(f"LLM cleanup error: {e}")
            return False
            
    def run_merge_step(self, output_folder):
        """
        Run merge step to fix content split across pages.
        
        Args:
            output_folder (Path): Directory containing JSON files to merge
            
        Returns:
            bool: True if successful, False if failed or cancelled
        """
        try:
            # Find all JSON files
            json_files = list(output_folder.glob("*.json"))
            json_files.sort()
            
            if not json_files:
                self._log("No JSON files found for merge step")
                return True
                
            self._log(f"Starting merge step with {len(json_files)} files...")
            
            sections = []
            
            for i, json_file in enumerate(json_files):
                if self.is_cancelled:
                    return False
                    
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        section = json.load(f)
                        
                    if len(section) == 0:
                        self._log(f"No sections in {json_file.name}, skipping")
                        continue
                        
                    if len(sections) == 0:
                        sections = section
                        continue
                        
                    # Check if merge is likely needed before calling LLM
                    last_section_content = sections[-1]["content"]
                    first_new_section_content = section[0]["content"]
                    
                    # If last section ends with punctuation and new section starts with capital letter,
                    # assume no merge needed
                    ends_with_punctuation = last_section_content and last_section_content[-1] in ['.', '!', '?', ':', ';']
                    starts_with_capital = first_new_section_content and first_new_section_content[0].isupper()
                    
                    if ends_with_punctuation and starts_with_capital:
                        self._log(f"No merge likely needed for {json_file.name}")
                        sections = sections + section
                        continue
                        
                    # Call LLM to determine if merge is needed
                    self._log(f"Checking merge for {json_file.name}...")
                    
                    merge_prompt = """These are two segments of text from an OCR task. The first segment is from the end of one page. The last segment is
from the beginning of the following page. Sometimes during OCR content is split between one page, and the next. We
need to identify when this happens, and join the content is necessary.

Examples:

## Example Of Split Content That Needs To Be Joined
First and second page segments
[
{"type":"paragraph","content":"Books are comprised of words on a page"},
{"type":"paragraph","content":"that make up long sentences of text."},
]

To join these sections, output this
action("merge")

## Example Of Segments that Should Not Be Joined
First and second page segments
[
{"type":"paragraph","content":"Books are comprised of words on a page that make up long sentences of text."},
{"type":"paragraph","content":"In this second paragraph, I shall refute the statement from the first."},
]

To leave as is, output this
action("noop")
"""
                    
                    payload = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": merge_prompt + "\n\n# SEGMENTS FROM FIRST AND NEXT PAGE\n\n" + json.dumps([sections[-1], section[0]])
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 20000,
                        "response_format": {
                            "type": "json_object"
                        }
                    }
                    
                    response = requests.post(
                        self.api_url,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.api_token}"
                        },
                        json=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        msg_content = response_data['choices'][0]['message']['content']
                        
                        if 'action("merge")' in msg_content:
                            self._log(f"Merging sections from {json_file.name}")
                            sections[-1]["content"] = sections[-1]["content"] + " " + section[0]["content"]
                            section = section[1:]
                        else:
                            self._log(f"No merge needed for {json_file.name}")
                            
                        sections = sections + section
                        
                    else:
                        self._log(f"API error for {json_file.name}: {response.status_code}")
                        sections = sections + section  # Continue without merge
                        
                except Exception as e:
                    self._log(f"Error processing {json_file.name}: {e}")
                    continue
                    
            # Save the merged result
            book_json_path = output_folder / "book.json"
            with open(book_json_path, 'w', encoding='utf-8') as f:
                json.dump(sections, f, indent=2, ensure_ascii=False)
                
            self._log(f"Merge completed! Saved {len(sections)} sections to book.json")
            return True
            
        except Exception as e:
            self._log(f"Merge step error: {e}")
            return False
            
    def process_single_file(self, txt_file):
        """
        Process a single text file with LLM cleanup.
        
        Args:
            txt_file (Path): Path to the text file to process
            
        Returns:
            bool: True if successful, False if failed
        """
        try:
            # Check if corresponding image and JSON files exist
            img_file = txt_file.with_suffix('.png')
            json_file = txt_file.with_suffix('.json')
            
            # Debug logging
            self._log(f"Processing {txt_file.name} -> {json_file.name}")
            
            if not img_file.exists():
                # Try other image extensions
                for ext in ['.jpg', '.jpeg', '.bmp', '.tiff']:
                    alt_img = txt_file.with_suffix(ext)
                    if alt_img.exists():
                        img_file = alt_img
                        break
                else:
                    self._log(f"No image file found for {txt_file.name}")
                    return False
                    
            if json_file.exists():
                self._log(f"Skipping {txt_file.name} - already processed")
                return True  # Already processed
                
            # Read the image and text files
            with open(img_file, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode("utf-8")
                
            with open(txt_file, "r", encoding='utf-8') as f:
                text_content = f.read()
                
            # Prepare API request
            ocr_prompt = """These images are segments of a book we are converting into structured json. Ensure that all content from 
the page is included, such as headers, subtexts, graphics (with alt text if possible), tables, and any other 
elements. You will be provided the output of the first pass of running OCR on these pages.

Requirements:
  - Output Only JSON: Return solely the JSON content without any additional explanations or comments.
  - No Delimiters: Do not use code fences or delimiters like ```markdown.
  - Complete Content: If present, do not omit any part of the page, including headers, block quotes, and subtext.
  - Accurate Content: Do not include parts that don't exist. If there is no header, footers, etc., do not include them.
  - Correct any OCR mistakes, including spelling, incorrect line breaks, or invalid characters.

Style Guide
  - Output as an array of objects. In the format of {"type":"section_type","content":"section content"}
  - Types should be title, author, header, sub_header, chapter_header, paragraph, page_division, bold, block_indent.
  - Ensure that your json strings are properly escaped and encoded.

Example:
[
{"type":"author","content":"A. Writer"},
{"type":"title","content":"The Great Book Title"},
{"type":"sub_header","content":"A guide to writing great book title"},
{"type":"chapter_header","content":"1"},
{"type":"paragraph","content":"Books are comprised of words on a page."},
{"type":"block_indent","content":"'This is a famous quote' - Some Guy"},
{"type":"paragraph","content":"Some additional \"words\" go in a paragraph."}
]
"""
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": ocr_prompt + "\n\n# OCR CONTENT\n\n" + text_content
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{encoded_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 20000,
                "response_format": {
                    "type": "json_object"
                }
            }
            
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_token}"
                },
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                response_data = response.json()
                msg_content = response_data['choices'][0]['message']['content']
                
                try:
                    parsed = json.loads(msg_content)
                    if isinstance(parsed, dict) and 'content' in parsed:
                        parsed = parsed['content']
                    if not isinstance(parsed, list):
                        parsed = [parsed]
                        
                    # Add source information
                    for item in parsed:
                        if isinstance(item, dict):
                            item["source"] = txt_file.name
                            
                    # Save JSON output
                    with open(json_file, "w", encoding='utf-8') as f:
                        json.dump(parsed, f, indent=2, ensure_ascii=False)
                    
                    self._log(f"Saved {len(parsed)} sections to {json_file.name}")
                    return True
                    
                except json.JSONDecodeError as e:
                    # Try to handle the failure
                    return self.handle_json_failure(payload, msg_content, str(e), json_file, txt_file.name)
                    
            else:
                return False
                
        except Exception as e:
            return False
            
    def handle_json_failure(self, payload, failed_json, exception_message, json_file, source_name):
        """
        Handle JSON parsing failures by retrying with error context.
        
        Args:
            payload (dict): Original API request payload
            failed_json (str): The failed JSON response
            exception_message (str): Error message from JSON parsing
            json_file (Path): Path to save the corrected JSON
            source_name (str): Name of the source file for logging
            
        Returns:
            bool: True if retry successful, False if failed
        """
        try:
            payload["messages"].append({
                "role": "assistant",
                "content": [{"type": "text", "text": failed_json}]
            })
            payload["messages"].append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"There was an error parsing your json, {exception_message}. Ensure that you've properly escaped your json strings."
                }]
            })
            
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_token}"
                },
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                response_data = response.json()
                msg_content = response_data['choices'][0]['message']['content']
                
                parsed = json.loads(msg_content)
                if isinstance(parsed, dict) and 'content' in parsed:
                    parsed = parsed['content']
                if not isinstance(parsed, list):
                    parsed = [parsed]
                    
                # Add source information
                for item in parsed:
                    if isinstance(item, dict):
                        item["source"] = source_name
                        
                # Save JSON output
                with open(json_file, "w", encoding='utf-8') as f:
                    json.dump(parsed, f, indent=2, ensure_ascii=False)
                
                self._log(f"Retry saved {len(parsed)} sections to {json_file.name}")
                return True
                
        except Exception:
            pass
            
        return False
        
    def test_api_connection(self):
        """
        Test the API connection with a simple request.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.api_url or not self.api_token:
            return False, "API URL and Token are required"
            
        try:
            # Simple test request
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": [{"type": "text", "text": "Hello"}]}],
                "max_tokens": 10
            }
            
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_token}"
                },
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, "API connection successful!"
            else:
                return False, f"API connection failed: {response.status_code}\n{response.text}"
                
        except Exception as e:
            return False, f"Failed to connect to API: {e}"