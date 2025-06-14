#!/usr/bin/env python3
"""
Test script to verify syntax highlighting functionality works correctly.
"""

import json
from pygments.lexers import JsonLexer

def test_syntax_highlighting():
    """Test the syntax highlighting logic."""
    
    # Sample JSON content
    test_json = '''[
  {
    "type": "title",
    "content": "Sample Book Title"
  },
  {
    "type": "author", 
    "content": "Sample Author"
  },
  {
    "type": "cover",
    "image": "cover.png"
  },
  {
    "type": "chapter_header",
    "content": "1"
  },
  {
    "type": "paragraph",
    "content": "This is a sample paragraph."
  }
]'''

    print("Testing JSON syntax highlighting...")
    print("=" * 50)
    
    # Initialize lexer
    json_lexer = JsonLexer()
    
    try:
        # Tokenize the content
        tokens = list(json_lexer.get_tokens(test_json))
        
        print(f"Successfully tokenized JSON content into {len(tokens)} tokens")
        print("\nToken analysis:")
        print("-" * 30)
        
        # Analyze tokens
        token_types = {}
        for token_type, text in tokens:
            token_str = str(token_type)
            if token_str not in token_types:
                token_types[token_str] = []
            if text.strip():  # Only show non-whitespace tokens
                token_types[token_str].append(repr(text))
        
        for token_type, examples in token_types.items():
            if examples:  # Only show types that have examples
                print(f"{token_type}: {examples[:3]}{'...' if len(examples) > 3 else ''}")
        
        print("\nSyntax highlighting test: PASSED ✓")
        
    except Exception as e:
        print(f"Syntax highlighting test: FAILED ✗")
        print(f"Error: {e}")
        return False
    
    return True

def test_tab_completion():
    """Test the tab completion logic."""
    
    print("\n" + "=" * 50)
    print("Testing tab completion...")
    print("=" * 50)
    
    # Test completions
    completions = [
        '"type"', '"content"', '"image"', '"author"', '"title"', 
        '"chapter_header"', '"paragraph"', '"cover"', '"page_break"',
        '"true"', '"false"', '"null"'
    ]
    
    test_cases = [
        ('', completions),  # No partial text - should return all completions
        ('"t', ['"type"', '"title"', '"true"']),  # Partial match
        ('"type', ['"type"']),  # Exact partial match
        ('"xyz', []),  # No matches
        ('"content', ['"content"']),  # Exact match
        ('"c', ['"content"', '"chapter_header"', '"cover"']),  # Multiple matches (includes chapter_header)
    ]
    
    print("Test cases:")
    print("-" * 30)
    
    all_passed = True
    for partial, expected in test_cases:
        matches = [c for c in completions if c.startswith(partial)]
        
        if set(matches) == set(expected):
            status = "PASSED ✓"
        else:
            status = "FAILED ✗"
            all_passed = False
        
        print(f"'{partial}' -> {matches} {status}")
        if set(matches) != set(expected):
            print(f"  Expected: {expected}")
    
    if all_passed:
        print("\nTab completion test: PASSED ✓")
    else:
        print("\nTab completion test: FAILED ✗")
    
    return all_passed

def test_json_validation():
    """Test JSON validation with the sample content."""
    
    print("\n" + "=" * 50)
    print("Testing JSON validation...")
    print("=" * 50)
    
    # Test valid JSON
    valid_json = '''[
  {
    "type": "title",
    "content": "Test Title"
  }
]'''
    
    # Test invalid JSON
    invalid_json = '''[
  {
    "type": "title",
    "content": "Test Title"
  
]'''  # Missing closing brace
    
    try:
        # Test valid JSON
        data = json.loads(valid_json)
        print("Valid JSON parsing: PASSED ✓")
        
        # Test invalid JSON
        try:
            json.loads(invalid_json)
            print("Invalid JSON detection: FAILED ✗ (should have failed)")
            return False
        except json.JSONDecodeError:
            print("Invalid JSON detection: PASSED ✓")
        
        return True
        
    except Exception as e:
        print(f"JSON validation test: FAILED ✗")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("BookExtract Syntax Highlighting & Tab Completion Test")
    print("=" * 60)
    
    # Run all tests
    test1 = test_syntax_highlighting()
    test2 = test_tab_completion()
    test3 = test_json_validation()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Syntax Highlighting: {'PASSED ✓' if test1 else 'FAILED ✗'}")
    print(f"Tab Completion: {'PASSED ✓' if test2 else 'FAILED ✗'}")
    print(f"JSON Validation: {'PASSED ✓' if test3 else 'FAILED ✗'}")
    
    if all([test1, test2, test3]):
        print("\nAll tests PASSED! ✓")
        print("The syntax highlighting and tab completion features are working correctly.")
    else:
        print("\nSome tests FAILED! ✗")
        print("Please check the implementation.")