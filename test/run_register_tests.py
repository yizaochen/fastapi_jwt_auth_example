#!/usr/bin/env python3
"""
Test runner for register endpoint tests.
This script runs the comprehensive test suite for the /register endpoint.
"""

import subprocess
import sys
import os


def run_register_tests():
    """Run the register endpoint tests"""
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Change to project root directory
    os.chdir(project_root)
    
    print("🧪 Running /register endpoint tests...")
    print("=" * 50)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test/register_test.py", 
            "-v",
            "--tb=short"
        ], check=True)
        
        print("\n" + "=" * 50)
        print("✅ All register tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print("❌ Some register tests failed!")
        print(f"Exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Make sure you have installed the development dependencies:")
        print("   uv sync --dev")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = run_register_tests()
    sys.exit(0 if success else 1)
