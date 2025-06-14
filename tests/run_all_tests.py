#!/usr/bin/env python3
"""
Comprehensive test runner for BookExtract project.

This script runs all unit tests and provides a summary of results.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and return results."""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        success = result.returncode == 0
        return {
            'file': test_file,
            'success': success,
            'duration': duration,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: {test_file} took longer than 60 seconds")
        return {
            'file': test_file,
            'success': False,
            'duration': 60.0,
            'returncode': -1,
            'stdout': '',
            'stderr': 'Test timed out after 60 seconds'
        }
    except Exception as e:
        print(f"❌ ERROR running {test_file}: {e}")
        return {
            'file': test_file,
            'success': False,
            'duration': 0.0,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

def main():
    """Run all tests and provide summary."""
    print("BookExtract Comprehensive Test Suite")
    print("=" * 60)
    
    # Find all test files
    test_files = [
        'test_intermediate.py',
        'test_epub_generator.py',
        'test_image_processor.py',
        'test_ocr_processor.py',
        'test_intermediate_to_m4b.py',
        'test_m4b_generator.py',
        'test_book_capture.py',
        'test_epub_generator_extended.py',
    ]
    
    # Check that all test files exist
    missing_files = []
    for test_file in test_files:
        if not os.path.exists(test_file):
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return 1
    
    # Run all tests
    results = []
    total_start_time = time.time()
    
    for test_file in test_files:
        result = run_test_file(test_file)
        results.append(result)
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"Total tests run: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total duration: {total_duration:.2f} seconds")
    print()
    
    # Detailed results
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = f"{result['duration']:.2f}s"
        print(f"{status} {result['file']} ({duration})")
        
        if not result['success']:
            print(f"    Return code: {result['returncode']}")
            if result['stderr']:
                print(f"    Error: {result['stderr'][:200]}...")
    
    print()
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())