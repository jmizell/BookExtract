#!/usr/bin/env python3
"""
Demo script to show what the syntax highlighting looks like in the terminal.
"""

import json
from pygments.lexers import JsonLexer
from pygments import highlight
from pygments.formatters import TerminalFormatter

def demo_syntax_highlighting():
    """Demonstrate syntax highlighting with colored terminal output."""
    
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
    "content": "Chapter 1"
  },
  {
    "type": "paragraph",
    "content": "This is a sample paragraph with some text content."
  },
  {
    "type": "paragraph",
    "content": "Another paragraph with numbers: 123, 456.789, and boolean values: true, false, null"
  }
]'''

    print("BookExtract JSON Editor - Syntax Highlighting Demo")
    print("=" * 60)
    print()
    print("Original JSON (without highlighting):")
    print("-" * 40)
    print(test_json)
    print()
    print("JSON with syntax highlighting (terminal colors):")
    print("-" * 40)
    
    # Apply syntax highlighting for terminal
    lexer = JsonLexer()
    formatter = TerminalFormatter()
    highlighted = highlight(test_json, lexer, formatter)
    print(highlighted)
    
    print("=" * 60)
    print("Features implemented:")
    print("✓ JSON syntax highlighting with different colors for:")
    print("  - Strings (red)")
    print("  - Numbers (blue)")
    print("  - Keywords like true/false/null (red)")
    print("  - Property names (green)")
    print("  - Punctuation (dark gray)")
    print()
    print("✓ Tab completion for common JSON schema keywords:")
    print("  - \"type\", \"content\", \"image\", \"author\", \"title\"")
    print("  - \"chapter_header\", \"paragraph\", \"cover\", \"page_break\"")
    print("  - \"true\", \"false\", \"null\"")
    print()
    print("✓ Real-time highlighting as you type")
    print("✓ Performance optimized to not slow down editing")
    print("✓ Error handling to prevent crashes during editing")

if __name__ == "__main__":
    demo_syntax_highlighting()