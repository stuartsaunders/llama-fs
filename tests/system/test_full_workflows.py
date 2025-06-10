#!/usr/bin/env python3
"""
Comprehensive system tests for LlamaFS FastAPI endpoints
Tests the full API surface with various scenarios
"""

import asyncio
import json
import os
import tempfile
import time
import requests
import sys
import pytest
from pathlib import Path

# Base URL for API
API_BASE = "http://127.0.0.1:8000"

@pytest.mark.system
def test_health_check():
    """Test basic server health"""
    print("🔍 Testing server health...")
    response = requests.get(f"{API_BASE}/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    print("✅ Server health check passed")

@pytest.mark.system
@pytest.mark.slow
def test_batch_endpoint_text_files():
    """Test batch endpoint with text files only"""
    print("🔍 Testing /batch endpoint with text files...")
    
    # Test with the text_files subdirectory (should be fast)
    payload = {
        "path": "/Users/stuartsaunders/Projects/llama-fs/sample_data/text_files",
        "instruction": "organize files",
        "incognito": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE}/batch", json=payload, timeout=60)
        duration = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Validate response structure
        for item in data:
            assert "src_path" in item
            assert "dst_path" in item
            assert "summary" in item
            assert isinstance(item["summary"], str)
            assert len(item["summary"]) > 0
        
        print(f"✅ /batch endpoint test passed ({duration:.1f}s)")
        print(f"   Processed {len(data)} files")
        for item in data:
            print(f"   {item['src_path']} → {item['dst_path']}")
        
    except Exception as e:
        print(f"❌ /batch endpoint test failed: {e}")
        pytest.fail(f"/batch endpoint test failed: {e}")

@pytest.mark.system
def test_batch_endpoint_invalid_path():
    """Test batch endpoint with invalid path"""
    print("🔍 Testing /batch endpoint with invalid path...")
    
    payload = {
        "path": "/nonexistent/path",
        "instruction": "organize files",
        "incognito": False
    }
    
    try:
        response = requests.post(f"{API_BASE}/batch", json=payload, timeout=30)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "does not exist" in data["detail"]
        
        print("✅ Invalid path handling test passed")
        
    except Exception as e:
        print(f"❌ Invalid path test failed: {e}")
        pytest.fail(f"Invalid path test failed: {e}")

@pytest.mark.system
def test_batch_endpoint_empty_directory():
    """Test batch endpoint with empty directory"""
    print("🔍 Testing /batch endpoint with empty directory...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "path": tmpdir,
            "instruction": "organize files",
            "incognito": False
        }
        
        try:
            response = requests.post(f"{API_BASE}/batch", json=payload, timeout=30)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0  # Empty directory should return empty list
            
            print("✅ Empty directory test passed")
            
        except Exception as e:
            print(f"❌ Empty directory test failed: {e}")
            pytest.fail(f"Empty directory test failed: {e}")

@pytest.mark.system
def test_commit_endpoint():
    """Test file commit endpoint"""
    print("🔍 Testing /commit endpoint...")
    
    # Create a test file to move
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create source file
        src_file = Path(tmpdir) / "test_file.txt"
        src_file.write_text("Test content for commit endpoint")
        
        # Create destination directory
        dst_dir = Path(tmpdir) / "organized"
        dst_dir.mkdir()
        
        payload = {
            "base_path": tmpdir,
            "src_path": "test_file.txt",
            "dst_path": "organized/test_file.txt"
        }
        
        try:
            # Verify source exists
            assert src_file.exists()
            
            # Make commit request
            response = requests.post(f"{API_BASE}/commit", json=payload, timeout=30)
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "successful" in data["message"]
            
            # Verify file was moved
            assert not src_file.exists()
            dst_file = Path(tmpdir) / "organized" / "test_file.txt"
            assert dst_file.exists()
            assert dst_file.read_text() == "Test content for commit endpoint"
            
            print("✅ /commit endpoint test passed")
            
        except Exception as e:
            print(f"❌ /commit endpoint test failed: {e}")
            pytest.fail(f"/commit endpoint test failed: {e}")

@pytest.mark.system
def test_commit_endpoint_invalid_source():
    """Test commit endpoint with invalid source file"""
    print("🔍 Testing /commit endpoint with invalid source...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "base_path": tmpdir,
            "src_path": "nonexistent_file.txt",
            "dst_path": "organized/file.txt"
        }
        
        try:
            response = requests.post(f"{API_BASE}/commit", json=payload, timeout=30)
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "does not exist" in data["detail"]
            
            print("✅ Invalid source file test passed")
            
        except Exception as e:
            print(f"❌ Invalid source file test failed: {e}")
            pytest.fail(f"Invalid source file test failed: {e}")

@pytest.mark.system
def test_malformed_requests():
    """Test API with malformed requests"""
    print("🔍 Testing malformed request handling...")
    
    test_cases = [
        # Missing required fields
        {"instruction": "organize"},  # Missing path
        {"path": "/tmp"},  # Missing instruction
        # Invalid JSON
        "invalid json",
        # Empty payload
        {},
    ]
    
    passed = 0
    for i, payload in enumerate(test_cases):
        try:
            if isinstance(payload, str):
                # Send invalid JSON
                response = requests.post(
                    f"{API_BASE}/batch", 
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            else:
                response = requests.post(f"{API_BASE}/batch", json=payload, timeout=10)
            
            # Should get 4xx error for malformed requests
            assert 400 <= response.status_code < 500
            passed += 1
            
        except Exception as e:
            print(f"   Test case {i+1} failed: {e}")
    
    if passed == len(test_cases):
        print("✅ Malformed request handling tests passed")
    else:
        print(f"❌ Only {passed}/{len(test_cases)} malformed request tests passed")
        pytest.fail(f"Only {passed}/{len(test_cases)} malformed request tests passed")

@pytest.mark.system
@pytest.mark.slow
def test_performance_metrics():
    """Test basic performance characteristics"""
    print("🔍 Testing performance metrics...")
    
    # Test with small directory
    payload = {
        "path": "/Users/stuartsaunders/Projects/llama-fs/sample_data/text_files",
        "instruction": "organize files",
        "incognito": False
    }
    
    times = []
    for i in range(3):
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE}/batch", json=payload, timeout=60)
            duration = time.time() - start_time
            times.append(duration)
            
            assert response.status_code == 200
            
        except Exception as e:
            print(f"❌ Performance test run {i+1} failed: {e}")
            pytest.fail(f"Performance test run {i+1} failed: {e}")
    
    avg_time = sum(times) / len(times)
    print(f"✅ Performance test passed")
    print(f"   Average response time: {avg_time:.2f}s")
    print(f"   Range: {min(times):.2f}s - {max(times):.2f}s")
    
    # Basic performance expectations
    if avg_time > 60:
        print("⚠️  Warning: Average response time > 60s (may be too slow)")

def run_all_system_tests():
    """Run all system tests"""
    print("LlamaFS System Tests")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_batch_endpoint_text_files,
        test_batch_endpoint_invalid_path,
        test_batch_endpoint_empty_directory,
        test_commit_endpoint,
        test_commit_endpoint_invalid_source,
        test_malformed_requests,
        test_performance_metrics,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
        print()  # Add spacing between tests
    
    print("=" * 50)
    print(f"System Tests Complete: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All system tests passed!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed")
        return False

if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get(f"{API_BASE}/", timeout=5)
    except requests.exceptions.RequestException:
        print("❌ FastAPI server not running on http://127.0.0.1:8000")
        print("   Start server with: fastapi dev server.py")
        sys.exit(1)
    
    # Run tests
    success = run_all_system_tests()
    sys.exit(0 if success else 1)