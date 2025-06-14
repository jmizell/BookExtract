#!/usr/bin/env python3
"""
Example usage of the modular EpubGenerator class.

This demonstrates how to use the EpubGenerator independently of the GUI.
"""

from render_epub import EpubGenerator
import tempfile
import os

def create_sample_book():
    """Create a sample EPUB book using the EpubGenerator."""
    
    # Sample book data in the expected format
    book_data = [
        {'type': 'title', 'content': 'The Adventures of Python'},
        {'type': 'author', 'content': 'Code Master'},
        {'type': 'cover', 'image': 'cover.png'},
        
        {'type': 'chapter_header', 'content': '1'},
        {'type': 'header', 'content': 'The Beginning'},
        {'type': 'paragraph', 'content': 'In the beginning, there was code. And the code was good.'},
        {'type': 'paragraph', 'content': 'Python slithered through the digital realm, bringing order to chaos.'},
        
        {'type': 'chapter_header', 'content': '2'},
        {'type': 'header', 'content': 'The Journey'},
        {'type': 'paragraph', 'content': 'Our hero embarked on a quest to refactor legacy code.'},
        {'type': 'bold', 'content': 'This was no ordinary task!'},
        {'type': 'block_indent', 'content': 'With great power comes great responsibility.'},
        
        {'type': 'page_division'},
        {'type': 'sub_header', 'content': 'A New Hope'},
        {'type': 'paragraph', 'content': 'Through modular design, the code became maintainable.'},
        
        {'type': 'chapter_header', 'content': '3'},
        {'type': 'header', 'content': 'The Resolution'},
        {'type': 'paragraph', 'content': 'And so, the EPUB generator was born, modular and reusable.'},
        {'type': 'paragraph', 'content': 'The end... or is it just the beginning?'},
    ]
    
    # Create a simple cover image (placeholder)
    cover_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x06\x00\x00\x00p\xe2\xf5$\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdab\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save cover image
        cover_path = os.path.join(temp_dir, 'cover.png')
        with open(cover_path, 'wb') as f:
            f.write(cover_data)
        
        # Create custom logger
        def my_logger(message, level="INFO"):
            print(f"📚 [{level}] {message}")
        
        # Create EPUB generator
        generator = EpubGenerator(logger=my_logger)
        
        # Generate EPUB
        output_path = os.path.join(temp_dir, 'sample_book.epub')
        print("🚀 Starting EPUB generation...")
        
        try:
            generator.generate_epub(book_data, output_path, temp_dir)
            
            # Copy to current directory for inspection
            import shutil
            final_path = './sample_book.epub'
            shutil.copy2(output_path, final_path)
            
            print(f"✅ EPUB created successfully: {final_path}")
            print(f"📊 File size: {os.path.getsize(final_path)} bytes")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def demonstrate_custom_logger():
    """Demonstrate using a custom logger with the EpubGenerator."""
    
    class BookLogger:
        def __init__(self):
            self.messages = []
        
        def log(self, message, level="INFO"):
            self.messages.append((level, message))
            if level == "ERROR":
                print(f"🚨 {message}")
            elif level == "WARNING":
                print(f"⚠️  {message}")
            else:
                print(f"ℹ️  {message}")
        
        def get_summary(self):
            return f"Logged {len(self.messages)} messages"
    
    # Simple test data
    test_data = [
        {'type': 'title', 'content': 'Logger Test'},
        {'type': 'author', 'content': 'Test Author'},
        {'type': 'cover', 'image': 'nonexistent.png'},  # This will trigger a warning
        {'type': 'paragraph', 'content': 'Test content'},
    ]
    
    logger = BookLogger()
    generator = EpubGenerator(logger=logger.log)
    
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as temp_file:
        try:
            generator.generate_epub(test_data, temp_file.name)
            print(f"📈 {logger.get_summary()}")
        except Exception as e:
            print(f"Expected error due to missing cover: {e}")
        finally:
            os.unlink(temp_file.name)

if __name__ == "__main__":
    print("🎯 EpubGenerator Example Usage\n")
    
    print("1. Creating a sample book:")
    create_sample_book()
    
    print("\n2. Demonstrating custom logger:")
    demonstrate_custom_logger()
    
    print("\n🎉 Examples completed!")