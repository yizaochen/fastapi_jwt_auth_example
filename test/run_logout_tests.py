#!/usr/bin/env python3
"""
Test runner for logout endpoint tests.
This script runs the comprehensive test suite for the /logout endpoint.
"""

import subprocess
import sys
import os


def run_logout_tests():
    """Run the logout endpoint tests"""
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Change to project root directory
    os.chdir(project_root)
    
    print("🧪 Running /logout endpoint tests with pytest fixtures...")
    print("=" * 60)
    
    try:
        # Run pytest with verbose output and show fixture setup
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test/logout_test.py", 
            "-v",
            "--tb=short",
            "-s"  # Show print statements from tests
        ], check=True)
        
        print("\n" + "=" * 60)
        print("✅ All logout tests with fixtures passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print("❌ Some logout tests failed!")
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
    success = run_logout_tests()
    sys.exit(0 if success else 1)
