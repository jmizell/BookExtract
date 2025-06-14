"""
Image Processing Module

This module handles image loading, processing, and crop operations.
It provides functionality for batch image cropping with preview capabilities.
"""

import glob
from pathlib import Path
from PIL import Image


class ImageProcessor:
    """Handles image loading, processing, and crop operations."""
    
    def __init__(self):
        self.image_files = []
        self.current_image_index = 0
        self.current_image = None
        
        # Default crop coordinates
        self.crop_x = 1056
        self.crop_y = 190
        self.crop_width = 822
        self.crop_height = 947
        
    def load_images_from_folder(self, input_folder):
        """Load images from the specified folder."""
        input_path = Path(input_folder)
        if not input_path.exists():
            raise FileNotFoundError(f"Input folder does not exist: {input_path}")
            
        # Find all image files
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff', '*.gif']
        self.image_files = []
        
        for ext in image_extensions:
            self.image_files.extend(glob.glob(str(input_path / ext)))
            self.image_files.extend(glob.glob(str(input_path / ext.upper())))
            
        if not self.image_files:
            raise ValueError(f"No image files found in {input_path}")
            
        self.image_files.sort()
        self.current_image_index = 0
        return len(self.image_files)
        
    def get_current_image_info(self):
        """Get information about the current image."""
        if not self.image_files:
            return None, "No images loaded"
            
        filename = Path(self.image_files[self.current_image_index]).name
        info = f"{self.current_image_index + 1}/{len(self.image_files)}: {filename}"
        return self.current_image_index, info
        
    def can_navigate_prev(self):
        """Check if we can navigate to previous image."""
        return self.current_image_index > 0
        
    def can_navigate_next(self):
        """Check if we can navigate to next image."""
        return self.current_image_index < len(self.image_files) - 1
        
    def navigate_prev(self):
        """Navigate to previous image."""
        if self.can_navigate_prev():
            self.current_image_index -= 1
            return True
        return False
        
    def navigate_next(self):
        """Navigate to next image."""
        if self.can_navigate_next():
            self.current_image_index += 1
            return True
        return False
        
    def load_current_image(self):
        """Load the current image and return it along with display info."""
        if not self.image_files:
            return None, None, None
            
        try:
            image_path = self.image_files[self.current_image_index]
            self.current_image = Image.open(image_path)
            
            # Calculate display size (max 600x400 while maintaining aspect ratio)
            max_width, max_height = 600, 400
            img_width, img_height = self.current_image.size
            
            scale = min(max_width / img_width, max_height / img_height, 1.0)
            display_width = int(img_width * scale)
            display_height = int(img_height * scale)
            
            # Resize image for display
            display_image = self.current_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            return self.current_image, display_image, scale
            
        except Exception as e:
            raise Exception(f"Could not load image: {e}")
            
    def set_crop_coordinates(self, x, y, width, height):
        """Set the crop coordinates."""
        self.crop_x = x
        self.crop_y = y
        self.crop_width = width
        self.crop_height = height
        
    def get_crop_coordinates(self):
        """Get the current crop coordinates."""
        return self.crop_x, self.crop_y, self.crop_width, self.crop_height
        
    def validate_crop_coordinates(self):
        """Validate crop coordinates."""
        if self.crop_x < 0 or self.crop_y < 0 or self.crop_width <= 0 or self.crop_height <= 0:
            raise ValueError("Invalid crop dimensions")
        return True
        
    def check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            from PIL import Image
            return True
        except ImportError:
            return False
            
    def process_images(self, output_folder, progress_callback=None):
        """Process all loaded images with the current crop settings."""
        if not self.image_files:
            raise ValueError("No images loaded")
            
        self.validate_crop_coordinates()
        
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        processed_count = 0
        
        for i, image_path in enumerate(self.image_files):
            if progress_callback:
                should_continue = progress_callback(i, f"Processing {i+1}/{len(self.image_files)}")
                if not should_continue:
                    break
                    
            try:
                input_path = Path(image_path)
                output_file = output_path / input_path.name
                
                # Use Pillow to crop the image
                with Image.open(input_path) as img:
                    # Define crop box (left, top, right, bottom)
                    crop_box = (self.crop_x, self.crop_y, 
                               self.crop_x + self.crop_width, 
                               self.crop_y + self.crop_height)
                    
                    # Ensure crop box is within image bounds
                    img_width, img_height = img.size
                    crop_box = (
                        max(0, min(crop_box[0], img_width)),
                        max(0, min(crop_box[1], img_height)),
                        max(0, min(crop_box[2], img_width)),
                        max(0, min(crop_box[3], img_height))
                    )
                    
                    # Crop and save the image
                    cropped_img = img.crop(crop_box)
                    cropped_img.save(output_file)
                    processed_count += 1
                
            except Exception as e:
                raise Exception(f"Error processing {input_path.name}: {e}")
                
        return processed_count