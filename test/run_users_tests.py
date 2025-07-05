#!/usr/bin/env python3
"""
Test runner for users endpoint tests.
This script runs the comprehensive test suite for the /users endpoints.
"""

import subprocess
import sys
import os


def run_users_tests():
    """Run the users endpoint tests"""
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Change to project root directory
    os.chdir(project_root)
    
    print("🧪 Running /users endpoint tests...")
    print("=" * 50)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test/users_test.py", 
            "-v",
            "--tb=short"
        ], check=True)
        
        print("\n" + "=" * 50)
        print("✅ All users tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print("❌ Some users tests failed!")
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
    success = run_users_tests()
    sys.exit(0 if success else 1)
