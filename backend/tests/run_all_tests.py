#!/usr/bin/env python3
"""
Test runner to execute all tests in the backend test suite.

This script runs all test files and provides a comprehensive summary.
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

def run_test_file(test_file):
    """Run a single test file and capture results."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_file}")
    print(f"{'='*60}")
    
    try:
        # Get the directory containing the test file
        test_dir = Path(test_file).parent.absolute()
        
        # Run the test file as a subprocess, ensuring we're in the right directory
        result = subprocess.run(
            [sys.executable, test_file], 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5 minute timeout
            cwd=test_dir  # Set working directory to test directory
        )
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: {test_file}")
        
        return {
            'file': test_file,
            'success': success,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {test_file} took longer than 5 minutes")
        return {
            'file': test_file,
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': 'Test timed out after 5 minutes'
        }
    except Exception as e:
        print(f"❌ ERROR running {test_file}: {e}")
        return {
            'file': test_file,
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

def main():
    """Run all tests and provide summary."""
    print("🚀 Backend Test Suite Runner")
    print(f"⏰ Started: {datetime.now().isoformat()}")
    print("="*60)
    
    # Get all test files in the current directory
    test_files = [
        'test_weaviate_connection.py',
        'test_mistral_api.py', 
        'test_ai_assistant.py',
        'test_api.py'
    ]
    
    # Verify all test files exist
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return
    
    # Run all tests
    results = []
    start_time = time.time()
    
    for test_file in test_files:
        result = run_test_file(test_file)
        results.append(result)
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"⏰ Total Duration: {duration:.2f} seconds")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        exit_code = 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed:")
        for result in results:
            if not result['success']:
                print(f"   ❌ {result['file']} (exit code: {result['returncode']})")
                if result['stderr']:
                    print(f"      Error: {result['stderr'][:100]}...")
        exit_code = 1
    
    print(f"\n⏰ Completed: {datetime.now().isoformat()}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 