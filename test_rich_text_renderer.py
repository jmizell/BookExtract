#!/usr/bin/env python3
"""
Test script for the RichTextRenderer functionality
"""

import tkinter as tk
from bookextract import RichTextRenderer

def test_rich_text_renderer():
    """Test the RichTextRenderer with sample data."""
    
    # Create a simple tkinter window for testing
    root = tk.Tk()
    root.title("Rich Text Renderer Test")
    root.geometry("800x600")
    
    # Create a text widget
    text_widget = tk.Text(root, wrap=tk.WORD, font=("Georgia", 11))
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Initialize the renderer
    renderer = RichTextRenderer(text_widget, "/workspace/BookExtract/out")
    
    # Sample JSON data to test with
    sample_data = [
        {
            "type": "title",
            "content": "Sample Book Title"
        },
        {
            "type": "author",
            "content": "Sample Author"
        },
        {
            "type": "chapter_header",
            "content": "1"
        },
        {
            "type": "paragraph",
            "content": "This is a sample paragraph to test the rich text rendering functionality."
        },
        {
            "type": "header",
            "content": "Sample Header"
        },
        {
            "type": "paragraph",
            "content": "Another paragraph with some content to demonstrate the formatting."
        },
        {
            "type": "bold",
            "content": "This text should appear in bold formatting."
        },
        {
            "type": "block_indent",
            "content": "This is an indented block of text that should appear with different margins."
        },
        {
            "type": "page_division"
        },
        {
            "type": "paragraph",
            "content": "Text after a page division."
        }
    ]
    
    # Render the sample data
    try:
        renderer.render_json_data(sample_data)
        print("✓ Successfully rendered sample JSON data")
    except Exception as e:
        print(f"✗ Error rendering JSON data: {e}")
        return False
    
    # Add a button to close the test
    close_button = tk.Button(root, text="Close Test", command=root.destroy)
    close_button.pack(pady=5)
    
    print("✓ Rich text renderer test window created")
    print("  Close the window to continue...")
    
    # Run the GUI (this will block until window is closed)
    root.mainloop()
    
    return True

if __name__ == "__main__":
    print("Testing RichTextRenderer...")
    success = test_rich_text_renderer()
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")