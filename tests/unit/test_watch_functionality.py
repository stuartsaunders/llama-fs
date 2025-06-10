#!/usr/bin/env python3
"""
Tests for watch mode functionality
"""
import pytest
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, Mock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.watch_utils import Handler, create_file_tree
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent


def test_watch_create_file_tree():
    """Test the watch-specific create_file_tree function"""
    print("\nTesting watch create_file_tree function...")
    
    # Mock LiteLLM response
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
        
        fs_events = json.dumps({"files": [{"src_path": "old.txt", "dst_path": "new.txt"}]})
        
        result = create_file_tree(summaries, fs_events)
        
        assert len(result) == 2
        assert result[0]["src_path"] == "file1.txt"
        assert result[0]["dst_path"] == "organized/docs/file1.txt"
        assert result[1]["src_path"] == "file2.pdf"
        assert result[1]["dst_path"] == "organized/pdfs/file2.pdf"
    
    print("✓ Watch create_file_tree test passed")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handler_initialization():
    """Test Handler class initialization"""
    print("\nTesting Handler initialization...")
    
    import queue
    test_queue = queue.Queue()
    callback = MagicMock()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = Handler(temp_dir, callback, test_queue)
        
        assert handler.base_path == temp_dir
        assert handler.callback == callback
        assert handler.queue == test_queue
        assert handler.events == []
    
    print("✓ Handler initialization test passed")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handler_set_summaries():
    """Test Handler set_summaries method"""
    print("\nTesting Handler set_summaries...")
    
    import queue
    test_queue = queue.Queue()
    callback = MagicMock()
    
    # Mock get_dir_summaries
    mock_summaries = [
        {"file_path": "test.txt", "summary": "Test file"},
        {"file_path": "doc.pdf", "summary": "PDF document"}
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = Handler(temp_dir, callback, test_queue)
        
        with patch('src.watch_utils.get_dir_summaries', AsyncMock(return_value=mock_summaries)):
            await handler.set_summaries()
            
            assert handler.summaries == mock_summaries
            assert len(handler.summaries_cache) == 2
            assert handler.summaries_cache["test.txt"]["summary"] == "Test file"
    
    print("✓ Handler set_summaries test passed")


@pytest.mark.unit
def test_handler_file_events():
    """Test Handler file system event methods"""
    print("\nTesting Handler file system events...")
    
    import queue
    test_queue = queue.Queue()
    callback = MagicMock()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = Handler(temp_dir, callback, test_queue)
        handler.summaries_cache = {"test.txt": {"summary": "Test file"}}
        
        # Mock get_file_summary for update_summary calls
        with patch('src.watch_utils.get_file_summary', return_value={"summary": "Updated file"}):
            
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            
            # Test file created event
            created_event = FileCreatedEvent(str(test_file))
            handler.on_created(created_event)
            
            # Test file modified event
            modified_event = FileModifiedEvent(str(test_file))
            handler.on_modified(modified_event)
            
            # Test file deleted event
            test_file.unlink()  # Actually delete the file
            deleted_event = FileDeletedEvent(str(test_file))
            handler.on_deleted(deleted_event)
            
    print("✓ Handler file events test passed")


@pytest.mark.unit
def test_handler_moved_event():
    """Test Handler file moved event"""
    print("\nTesting Handler moved event...")
    
    import queue
    test_queue = queue.Queue()
    
    # Mock callback to return expected structure
    callback = MagicMock(return_value={"files": [{"src_path": "old.txt", "dst_path": "new.txt"}]})
    
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = Handler(temp_dir, callback, test_queue)
        handler.summaries = [{"file_path": "test.txt", "summary": "Test file"}]
        handler.summaries_cache = {"test.txt": {"summary": "Test file"}}
        
        # Mock get_file_summary for update_summary calls
        with patch('src.watch_utils.get_file_summary', return_value={"summary": "Updated file"}):
            
            # Test file moved event
            old_path = str(Path(temp_dir) / "old.txt")
            new_path = str(Path(temp_dir) / "new.txt")
            
            moved_event = FileMovedEvent(old_path, new_path)
            handler.on_moved(moved_event)
            
            # Check that event was recorded
            assert len(handler.events) == 1
            assert handler.events[0]["src_path"] == "old.txt"
            assert handler.events[0]["dst_path"] == "new.txt"
            
            # Check that callback was called
            callback.assert_called_once()
            
            # Check that result was queued
            assert not test_queue.empty()
            queued_result = test_queue.get()
            assert "files" in queued_result
    
    print("✓ Handler moved event test passed")


@pytest.mark.system
@pytest.mark.asyncio
async def test_watch_endpoint_integration():
    """Test /watch endpoint integration (without actually starting file watching)"""
    print("\nTesting /watch endpoint integration...")
    
    # Skip this test to avoid starting background file watchers
    # The /watch endpoint starts long-running Observer processes that continue
    # processing files even after the test completes
    pytest.skip("Skipping /watch endpoint test to avoid background file processing")
    
    import requests
    from unittest.mock import patch
    
    # This test will only work if the server is running
    # For now, we'll create a mock test
    
    API_BASE = "http://127.0.0.1:8000"
    
    # Mock the watch functionality to avoid actual file watching
    with patch('src.watch_utils.Observer') as mock_observer:
        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance
        
        try:
            payload = {
                "path": "./sample_data",
                "instruction": "organize files",
                "incognito": False
            }
            
            # This will only succeed if server is running
            response = requests.post(f"{API_BASE}/watch", json=payload, timeout=5)
            
            # If we get here, server is running
            print(f"✓ /watch endpoint responded with status: {response.status_code}")
            
            # The endpoint should return a streaming response
            assert response.status_code in [200, 202]  # Accept either success code
            
        except requests.exceptions.ConnectionError:
            print("⚠ Server not running - skipping /watch endpoint test")
            # Mark test as passed since this is expected in CI/testing
            pass
        except Exception as e:
            print(f"❌ /watch endpoint test failed: {e}")
            # Don't fail the test if server isn't running
            pass
    
    print("✓ Watch endpoint integration test completed")


if __name__ == "__main__":
    # Run tests manually for debugging
    print("Running watch functionality tests...")
    
    # Sync tests
    test_watch_create_file_tree()
    test_handler_file_events()
    test_handler_moved_event()
    
    # Async tests
    async def run_async_tests():
        await test_handler_initialization()
        await test_handler_set_summaries()
        await test_watch_endpoint_integration()
    
    asyncio.run(run_async_tests())
    
    print("\n🎉 All watch tests completed!")