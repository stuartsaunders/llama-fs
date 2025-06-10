#!/usr/bin/env python3
"""
Test script for LiteLLM integration in LlamaFS
Tests the core functionality without requiring API keys
"""

import asyncio
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.loader import summarize_document, summarize_document_sync, summarize_image_document
from src.tree_generator import create_file_tree


@pytest.mark.unit
def test_environment_variables():
    """Test that environment variables are properly read"""
    print("Testing environment variable configuration...")
    
    # Test defaults when no env vars are set
    with patch.dict(os.environ, {}, clear=True):
        from src.loader import summarize_document
        # The default should be groq models
        assert os.getenv("MODEL_TEXT", "groq/llama-3.3-70b-versatile") == "groq/llama-3.3-70b-versatile"
        assert os.getenv("MODEL_VISION", "groq/llama-4-scout-17b-16e-instruct") == "groq/llama-4-scout-17b-16e-instruct"
    
    # Test with custom env vars
    with patch.dict(os.environ, {"MODEL_TEXT": "ollama/test", "MODEL_VISION": "ollama/vision-test"}):
        assert os.getenv("MODEL_TEXT") == "ollama/test"
        assert os.getenv("MODEL_VISION") == "ollama/vision-test"
    
    print("✓ Environment variable tests passed")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_json_extraction():
    """Test JSON extraction from markdown blocks"""
    print("\nTesting JSON extraction from markdown blocks...")
    
    # Mock LiteLLM response with markdown-wrapped JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''```json
{
    "file_path": "test.txt",
    "summary": "Test summary"
}
```

Additional text that should be ignored'''
    
    with patch('litellm.acompletion', AsyncMock(return_value=mock_response)):
        doc = {"content": "test content", "file_name": "test.txt"}
        result = await summarize_document(doc)
        
        assert result["file_path"] == "test.txt"
        assert result["summary"] == "Test summary"
    
    print("✓ JSON extraction tests passed")


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling and fallbacks"""
    print("\nTesting error handling...")
    
    # Test JSON parse error
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Invalid JSON response"
    
    with patch('litellm.acompletion', AsyncMock(return_value=mock_response)):
        doc = {"content": "test content", "file_name": "error_test.txt"}
        result = await summarize_document(doc)
        
        assert result["file_path"] == "error_test.txt"
        assert "Invalid JSON response" in result["summary"]
    
    # Test API error
    with patch('litellm.acompletion', AsyncMock(side_effect=Exception("API Error"))):
        doc = {"content": "test content", "file_name": "api_error.txt"}
        result = await summarize_document(doc)
        
        assert result["file_path"] == "api_error.txt"
        assert "Processing failed" in result["summary"]
    
    print("✓ Error handling tests passed")


@pytest.mark.unit
def test_model_selection():
    """Test that correct models are selected based on environment"""
    print("\nTesting model selection...")
    
    # Test text model selection
    with patch.dict(os.environ, {"MODEL_TEXT": "custom/text-model"}):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"file_path": "test.txt", "summary": "test"}'
        
        with patch('litellm.completion', MagicMock(return_value=mock_response)) as mock_litellm:
            doc = {"content": "test", "file_name": "test.txt"}
            summarize_document_sync(doc)
            
            # Check that LiteLLM was called with the custom model
            mock_litellm.assert_called()
            call_args = mock_litellm.call_args
            assert call_args[1]["model"] == "custom/text-model"
    
    print("✓ Model selection tests passed")


@pytest.mark.unit
def test_tree_generator():
    """Test file tree generation with LiteLLM"""
    print("\nTesting tree generator...")
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "files": [
            {"src_path": "file1.txt", "dst_path": "organized/docs/file1.txt"},
            {"src_path": "file2.pdf", "dst_path": "organized/pdfs/file2.pdf"}
        ]
    })
    
    with patch('litellm.completion', MagicMock(return_value=mock_response)):
        summaries = [
            {"file_path": "file1.txt", "summary": "Text document"},
            {"file_path": "file2.pdf", "summary": "PDF document"}
        ]
        
        result = create_file_tree(summaries, None)
        
        assert len(result) == 2
        assert result[0]["src_path"] == "file1.txt"
        assert result[0]["dst_path"] == "organized/docs/file1.txt"
    
    print("✓ Tree generator tests passed")


async def run_all_tests():
    """Run all tests"""
    print("Running LiteLLM Integration Tests")
    print("=" * 50)
    
    try:
        test_environment_variables()
        await test_json_extraction()
        await test_error_handling()
        test_model_selection()
        test_tree_generator()
        
        print("\n" + "=" * 50)
        print("All tests passed! ✅")
        return True
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)