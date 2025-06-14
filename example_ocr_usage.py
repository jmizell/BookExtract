#!/usr/bin/env python3
"""
Example usage of the modular OCR processor.

This demonstrates how to use the OCRProcessor class independently of the GUI.
"""

from pathlib import Path
from ocr_processor import OCRProcessor


def main():
    """Example of using OCRProcessor without GUI."""
    
    # Initialize the processor
    processor = OCRProcessor(
        api_url="your_api_url_here",
        api_token="your_api_token_here", 
        model="your_model_here",
        max_workers=5
    )
    
    # Set up callbacks for logging and progress
    def log_message(message):
        print(f"[LOG] {message}")
        
    def update_progress(current, status):
        print(f"[PROGRESS] {current}: {status}")
    
    processor.set_callbacks(
        progress_callback=update_progress,
        log_callback=log_message
    )
    
    # Define input and output folders
    input_folder = Path("input_images")
    output_folder = Path("output_results")
    
    # Create output folder if it doesn't exist
    output_folder.mkdir(exist_ok=True)
    
    # Test API connection first
    print("Testing API connection...")
    success, message = processor.test_api_connection()
    print(f"API Test: {message}")
    
    if not success:
        print("API connection failed. Please check your credentials.")
        return
    
    # Run basic OCR
    print("\nRunning basic OCR...")
    if processor.run_basic_ocr(input_folder, output_folder):
        print("Basic OCR completed successfully!")
        
        # Run LLM cleanup
        print("\nRunning LLM cleanup...")
        if processor.run_llm_cleanup(output_folder):
            print("LLM cleanup completed successfully!")
            
            # Run merge step
            print("\nRunning merge step...")
            if processor.run_merge_step(output_folder):
                print("Merge step completed successfully!")
                print(f"Results saved to: {output_folder}")
            else:
                print("Merge step failed!")
        else:
            print("LLM cleanup failed!")
    else:
        print("Basic OCR failed!")


if __name__ == "__main__":
    main()