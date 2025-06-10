#!/usr/bin/env python3
"""
Import validation tests to catch missing dependencies early
"""
import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.unit
def test_import_all_source_modules():
    """Test that all source modules can be imported without missing dependencies"""
    print("\nTesting import of all source modules...")
    
    try:
        # Test main server module
        import server
        print("✓ server.py imported successfully")
        
        # Test loader module
        from src import loader
        print("✓ src/loader.py imported successfully")
        
        # Test tree generator
        from src import tree_generator
        print("✓ src/tree_generator.py imported successfully")
        
        # Test watch utils (this was the problematic one)
        from src import watch_utils
        print("✓ src/watch_utils.py imported successfully")
        
        print("✅ All source modules imported successfully")
        
    except ImportError as e:
        pytest.fail(f"Import error: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing modules: {e}")


@pytest.mark.unit
def test_import_specific_classes_and_functions():
    """Test that specific classes and functions can be imported"""
    print("\nTesting specific imports...")
    
    try:
        # Test FastAPI app import
        from server import app
        print("✓ FastAPI app imported")
        
        # Test loader functions
        from src.loader import get_dir_summaries, summarize_document, extract_json_from_response
        print("✓ Loader functions imported")
        
        # Test tree generator
        from src.tree_generator import create_file_tree
        print("✓ Tree generator function imported")
        
        # Test watch utils
        from src.watch_utils import Handler, create_file_tree as watch_create_file_tree
        print("✓ Watch utils classes and functions imported")
        
        print("✅ All specific imports successful")
        
    except ImportError as e:
        pytest.fail(f"Specific import error: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error in specific imports: {e}")


@pytest.mark.unit
def test_critical_dependencies_available():
    """Test that critical external dependencies are available"""
    print("\nTesting critical dependencies...")
    
    critical_deps = [
        "fastapi",
        "litellm", 
        "llama_index",
        "watchdog",
        "ollama",
        "agentops"
    ]
    
    for dep in critical_deps:
        try:
            __import__(dep)
            print(f"✓ {dep} available")
        except ImportError:
            pytest.fail(f"Critical dependency missing: {dep}")
    
    print("✅ All critical dependencies available")


if __name__ == "__main__":
    # Run the tests manually
    test_import_all_source_modules()
    test_import_specific_classes_and_functions()
    test_critical_dependencies_available()
    print("\n🎉 All import tests passed!")