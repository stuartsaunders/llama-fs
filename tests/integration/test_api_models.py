#!/usr/bin/env python3
"""
Test script for real API calls with LiteLLM integration
Only runs if API keys are available
"""

import asyncio
import os
import sys
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.loader import get_dir_summaries, get_file_summary
from src.tree_generator import create_file_tree


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_with_real_api():
    """Test with real API if keys are available"""
    # Check if we have API keys
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    has_ollama = os.path.exists("/tmp/ollama.pid") or os.system("pgrep ollama > /dev/null 2>&1") == 0
    
    if not has_groq and not has_ollama:
        print("⚠️  No API keys or Ollama found. Skipping real API tests.")
        print("   Set GROQ_API_KEY or run Ollama locally to enable these tests.")
        return
    
    print(f"Running real API tests...")
    print(f"- Groq API: {'Available' if has_groq else 'Not available'}")
    print(f"- Ollama: {'Running' if has_ollama else 'Not running'}")
    
    # Create a temporary test directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        test_files = {
            "meeting_notes.txt": "Team meeting notes from January 15, 2024. Discussed Q1 roadmap and budget allocation.",
            "invoice_2024.txt": "Invoice #1234 for consulting services. Amount: $5000. Due date: February 1, 2024.",
            "readme.txt": "This is the README file for the project. It contains installation instructions.",
        }
        
        for filename, content in test_files.items():
            with open(os.path.join(tmpdir, filename), "w") as f:
                f.write(content)
        
        print(f"\nCreated test files in {tmpdir}")
        
        # Test directory summarization
        print("\nTesting directory summarization...")
        summaries = await get_dir_summaries(tmpdir)
        
        assert len(summaries) == 3, f"Expected 3 summaries, got {len(summaries)}"
        
        for summary in summaries:
            print(f"- {summary['file_path']}: {summary['summary'][:50]}...")
        
        # Test file tree generation
        print("\nTesting file organization suggestions...")
        file_tree = create_file_tree(summaries, None)
        
        print("\nSuggested organization:")
        for item in file_tree:
            print(f"- {item['src_path']} → {item['dst_path']}")
        
        # Test single file processing
        print("\nTesting single file processing...")
        single_summary = get_file_summary(os.path.join(tmpdir, "meeting_notes.txt"))
        assert "meeting" in single_summary["summary"].lower() or "team" in single_summary["summary"].lower()
        
    print("\n✅ Real API tests completed successfully!")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_with_different_models():
    """Test with different model configurations"""
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  Skipping model comparison tests (no GROQ_API_KEY)")
        return
    
    print("\nTesting with different models...")
    
    test_doc = {"content": "Artificial intelligence and machine learning are transforming industries.", "file_name": "ai_article.txt"}
    
    # Save current model
    original_model = os.getenv("MODEL_TEXT")
    
    try:
        # Test with different models if available
        models_to_test = []
        
        if os.getenv("GROQ_API_KEY"):
            models_to_test.append("groq/llama-3.3-70b-versatile")
        
        if os.system("pgrep ollama > /dev/null 2>&1") == 0:
            models_to_test.append("ollama/llama3.2")
        
        for model in models_to_test:
            print(f"\nTesting with model: {model}")
            os.environ["MODEL_TEXT"] = model
            
            from src.loader import summarize_document
            result = await summarize_document(test_doc)
            print(f"Summary: {result['summary'][:80]}...")
            
    finally:
        # Restore original model
        if original_model:
            os.environ["MODEL_TEXT"] = original_model
        elif "MODEL_TEXT" in os.environ:
            del os.environ["MODEL_TEXT"]


async def main():
    """Run all real API tests"""
    print("LiteLLM Integration - Real API Tests")
    print("=" * 50)
    
    try:
        await test_with_real_api()
        await test_with_different_models()
        
        print("\n" + "=" * 50)
        print("All real API tests completed! ✅")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)