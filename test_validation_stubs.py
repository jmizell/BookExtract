#!/usr/bin/env python3
"""
Test script for the validation stub insertion functionality.
This tests the JSON validation and stub insertion without GUI.
"""

import json

def test_validation_logic():
    """Test the validation logic that will be used in the GUI."""
    
    print("Testing JSON validation and stub insertion logic...")
    
    # Test case 1: Missing all required sections
    test_json_1 = [
        {"type": "paragraph", "content": "Some content"}
    ]
    
    print("\nTest 1: Missing all required sections")
    print("Original JSON:", json.dumps(test_json_1, indent=2))
    
    # Simulate validation logic
    has_title = any(item.get('type') == 'title' for item in test_json_1)
    has_author = any(item.get('type') == 'author' for item in test_json_1)
    has_cover = any(item.get('type') == 'cover' for item in test_json_1)
    
    missing_sections = []
    if not has_title:
        missing_sections.append("title")
    if not has_author:
        missing_sections.append("author")
    if not has_cover:
        missing_sections.append("cover")
    
    print(f"Missing sections: {missing_sections}")
    
    # Simulate stub insertion
    if missing_sections:
        new_data = []
        
        if not has_title:
            new_data.append({
                "type": "title",
                "content": "Your Book Title Here"
            })
            
        if not has_author:
            new_data.append({
                "type": "author", 
                "content": "Your Name Here"
            })
            
        if not has_cover:
            new_data.append({
                "type": "cover",
                "image": "cover.png"
            })
        
        # Add existing data
        new_data.extend(test_json_1)
        
        print("JSON with stubs added:")
        print(json.dumps(new_data, indent=2))
    
    # Test case 2: Missing only title and author
    test_json_2 = [
        {"type": "cover", "image": "my_cover.png"},
        {"type": "paragraph", "content": "Some content"}
    ]
    
    print("\n" + "="*50)
    print("Test 2: Missing title and author only")
    print("Original JSON:", json.dumps(test_json_2, indent=2))
    
    # Simulate validation logic
    has_title = any(item.get('type') == 'title' for item in test_json_2)
    has_author = any(item.get('type') == 'author' for item in test_json_2)
    has_cover = any(item.get('type') == 'cover' for item in test_json_2)
    
    missing_sections = []
    if not has_title:
        missing_sections.append("title")
    if not has_author:
        missing_sections.append("author")
    if not has_cover:
        missing_sections.append("cover")
    
    print(f"Missing sections: {missing_sections}")
    
    # Simulate stub insertion
    if missing_sections:
        new_data = []
        
        if not has_title:
            new_data.append({
                "type": "title",
                "content": "Your Book Title Here"
            })
            
        if not has_author:
            new_data.append({
                "type": "author", 
                "content": "Your Name Here"
            })
            
        if not has_cover:
            new_data.append({
                "type": "cover",
                "image": "cover.png"
            })
        
        # Add existing data
        new_data.extend(test_json_2)
        
        print("JSON with stubs added:")
        print(json.dumps(new_data, indent=2))
    
    # Test case 3: All required sections present
    test_json_3 = [
        {"type": "title", "content": "My Book"},
        {"type": "author", "content": "John Doe"},
        {"type": "cover", "image": "cover.png"},
        {"type": "paragraph", "content": "Some content"}
    ]
    
    print("\n" + "="*50)
    print("Test 3: All required sections present")
    print("Original JSON:", json.dumps(test_json_3, indent=2))
    
    # Simulate validation logic
    has_title = any(item.get('type') == 'title' for item in test_json_3)
    has_author = any(item.get('type') == 'author' for item in test_json_3)
    has_cover = any(item.get('type') == 'cover' for item in test_json_3)
    
    missing_sections = []
    if not has_title:
        missing_sections.append("title")
    if not has_author:
        missing_sections.append("author")
    if not has_cover:
        missing_sections.append("cover")
    
    if missing_sections:
        print(f"Missing sections: {missing_sections}")
    else:
        print("✓ All required sections present - no stubs needed")

def main():
    """Run validation tests."""
    print("=" * 60)
    print("Testing JSON Validation and Stub Insertion Logic")
    print("=" * 60)
    
    test_validation_logic()
    
    print("\n" + "=" * 60)
    print("Testing completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()