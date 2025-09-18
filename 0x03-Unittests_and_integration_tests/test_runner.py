#!/usr/bin/env python3
"""
Debug test runner to identify specific test failures
"""

import unittest
import sys
import traceback

if __name__ == '__main__':
    try:
        # Import test modules
        import test_client
        
        # Create test loader and discover all tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_client)
        
        # Run tests with maximum verbosity
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=False)
        result = runner.run(suite)
        
        # Print detailed results
        print(f"\nRan {result.testsRun} tests")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\n=== FAILURES ===")
            for test, trace in result.failures:
                print(f"FAIL: {test}")
                print(trace)
                print("-" * 70)
        
        if result.errors:
            print("\n=== ERRORS ===")
            for test, trace in result.errors:
                print(f"ERROR: {test}")
                print(trace)
                print("-" * 70)
                
        # Final status
        if result.wasSuccessful():
            print("OK")
        else:
            print("FAIL")
            
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure you have client.py, fixtures.py, and test_client.py in the same directory")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()