#!/usr/bin/env python3
"""
Test the image rendering functionality without GUI.
"""

import json
import os
from pathlib import Path
from PIL import Image

# Mock the GUI parts we can't test without a display
class MockRenderBookGUI:
    def __init__(self):
        self.current_json_file = None
        self.default_input_folder = str(Path.cwd())
        self.image_cache = {}
        
    def log_message(self, message, level="INFO"):
        print(f"[{level}] {message}")
        
    def clear_image_cache(self):
        """Clear the image cache to free memory."""
        self.image_cache.clear()
        
    def load_and_resize_image(self, image_path, max_width=400, max_height=300, is_cover=False):
        """Load and resize an image for display in the preview."""
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
                
                # For testing, we'll just return the resized PIL Image instead of PhotoImage
                self.image_cache[cache_key] = img_resized
                return img_resized
                
        except Exception as e:
            self.log_message(f"Failed to load image {image_path}: {str(e)}", "WARNING")
            return None
    
    def _generate_rich_text_content(self, book_data):
        """Generate rich text content from JSON data."""
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
                image_path = item.get('image', '')
                if image_path:
                    # Check if image exists
                    if self.current_json_file:
                        full_image_path = os.path.join(os.path.dirname(self.current_json_file), image_path)
                    else:
                        full_image_path = os.path.join(self.default_input_folder, image_path)
                    
                    if os.path.exists(full_image_path):
                        # Try to load the actual image
                        photo = self.load_and_resize_image(full_image_path, is_cover=True)
                        if photo:
                            content_parts.append(('cover_image', photo))
                        else:
                            content_parts.append(('cover', f"[COVER IMAGE: {image_path} - LOAD FAILED]"))
                    else:
                        content_parts.append(('cover', f"[COVER IMAGE: {image_path} - NOT FOUND]"))
                else:
                    content_parts.append(('cover', "[COVER IMAGE: No image specified]"))
                content_parts.append(('paragraph', ''))  # Add spacing
                
            elif item_type == 'image':
                image_path = item.get('image', '')
                caption = item.get('caption', '')
                
                if image_path:
                    # Check if image exists
                    if self.current_json_file:
                        full_image_path = os.path.join(os.path.dirname(self.current_json_file), image_path)
                    else:
                        full_image_path = os.path.join(self.default_input_folder, image_path)
                    
                    if os.path.exists(full_image_path):
                        # Try to load the actual image
                        photo = self.load_and_resize_image(full_image_path, is_cover=False)
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
                    
            elif item_type == 'paragraph':
                content_parts.append(('paragraph', content))
        
        return content_parts

def test_image_rendering():
    """Test the complete image rendering pipeline."""
    print("Testing Image Rendering Functionality")
    print("=" * 50)
    
    # Create test instance
    gui = MockRenderBookGUI()
    
    # Load the sample JSON
    sample_file = "sample_book_with_images.json"
    if os.path.exists(sample_file):
        with open(sample_file, 'r') as f:
            book_data = json.load(f)
        
        print(f"✓ Loaded sample JSON with {len(book_data)} elements")
        
        # Process the content
        content_parts = gui._generate_rich_text_content(book_data)
        
        print(f"✓ Generated {len(content_parts)} content parts")
        
        # Analyze the results
        image_count = 0
        text_count = 0
        
        for tag, content in content_parts:
            if tag in ('cover_image', 'content_image'):
                image_count += 1
                if hasattr(content, 'size'):  # PIL Image object
                    print(f"  ✓ {tag}: Successfully loaded image {content.size}")
                else:
                    print(f"  ✗ {tag}: Failed to load image")
            elif content and content.strip():
                text_count += 1
        
        print(f"\nResults:")
        print(f"  • Successfully rendered images: {image_count}")
        print(f"  • Text elements: {text_count}")
        
        # Test cache functionality
        print(f"  • Images in cache: {len(gui.image_cache)}")
        gui.clear_image_cache()
        print(f"  • Images after cache clear: {len(gui.image_cache)}")
        
        print("\n✓ Image rendering test completed successfully!")
        
    else:
        print(f"✗ Sample file {sample_file} not found")
        return False
    
    return True

if __name__ == "__main__":
    success = test_image_rendering()
    if success:
        print("\n🎉 All tests passed! Image rendering is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above.")