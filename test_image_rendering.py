#!/usr/bin/env python3
"""
Test script to verify image loading functionality without GUI.
"""

import os
import json
from pathlib import Path
from PIL import Image, ImageTk

def test_image_loading():
    """Test the image loading and resizing functionality."""
    
    def load_and_resize_image(image_path, max_width=400, max_height=300, is_cover=False):
        """Load and resize an image for display in the preview."""
        try:
            # Use larger dimensions for cover images
            if is_cover:
                max_width = 300
                max_height = 400
            
            print(f"Loading image: {image_path}")
            print(f"Max dimensions: {max_width}x{max_height}")
            
            # Load and process image
            with Image.open(image_path) as img:
                print(f"Original image size: {img.size}")
                print(f"Original image mode: {img.mode}")
                
                # Convert to RGB if necessary (handles RGBA, P mode, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                    print(f"Converted to RGB mode")
                
                # Calculate resize dimensions maintaining aspect ratio
                img_width, img_height = img.size
                width_ratio = max_width / img_width
                height_ratio = max_height / img_height
                ratio = min(width_ratio, height_ratio)
                
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                
                print(f"Resize ratio: {ratio:.3f}")
                print(f"New dimensions: {new_width}x{new_height}")
                
                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                print(f"✓ Successfully processed image: {image_path}")
                return True
                
        except Exception as e:
            print(f"✗ Failed to load image {image_path}: {str(e)}")
            return False

    # Test with some common image formats if they exist
    test_images = [
        "cover.png",
        "cover.jpg", 
        "cover.jpeg",
        "test.png",
        "test.jpg"
    ]
    
    print("Testing image loading functionality...")
    print("=" * 50)
    
    # Check current directory for any images
    current_dir = Path.cwd()
    found_images = []
    
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']:
        found_images.extend(current_dir.glob(ext))
    
    if found_images:
        print(f"Found {len(found_images)} images in current directory:")
        for img in found_images[:3]:  # Test first 3 images
            print(f"\nTesting: {img.name}")
            print("-" * 30)
            success = load_and_resize_image(str(img), is_cover=True)
            if success:
                print("✓ Image loading test passed")
            else:
                print("✗ Image loading test failed")
    else:
        print("No images found in current directory.")
        print("Creating a test image...")
        
        # Create a simple test image
        test_img = Image.new('RGB', (800, 600), color='lightblue')
        test_path = current_dir / "test_image.png"
        test_img.save(test_path)
        print(f"Created test image: {test_path}")
        
        print(f"\nTesting created image:")
        print("-" * 30)
        success = load_and_resize_image(str(test_path), is_cover=True)
        if success:
            print("✓ Image loading test passed")
        else:
            print("✗ Image loading test failed")
    
    print("\n" + "=" * 50)
    print("Image loading functionality test completed!")

def test_json_processing():
    """Test JSON processing with image elements."""
    print("\nTesting JSON processing with images...")
    print("=" * 50)
    
    # Sample JSON with images
    sample_json = [
        {
            "type": "title",
            "content": "Sample Book with Images"
        },
        {
            "type": "author",
            "content": "Test Author"
        },
        {
            "type": "cover",
            "image": "test_image.png"
        },
        {
            "type": "chapter_header",
            "content": "1"
        },
        {
            "type": "paragraph",
            "content": "This chapter contains an image below:"
        },
        {
            "type": "image",
            "image": "test_image.png",
            "caption": "A sample test image"
        },
        {
            "type": "paragraph",
            "content": "This is text after the image."
        }
    ]
    
    print("Sample JSON structure:")
    print(json.dumps(sample_json, indent=2))
    
    print("\nProcessing image elements...")
    for item in sample_json:
        if item.get('type') in ['cover', 'image']:
            image_path = item.get('image', '')
            if image_path:
                print(f"Found {item['type']} with image: {image_path}")
                if os.path.exists(image_path):
                    print(f"  ✓ Image file exists")
                else:
                    print(f"  ✗ Image file not found")
    
    print("JSON processing test completed!")

if __name__ == "__main__":
    test_image_loading()
    test_json_processing()