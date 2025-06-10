"""
Pytest configuration and fixtures for LlamaFS tests
"""
import os
import tempfile
import pytest
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing"""
    file_path = Path(temp_dir) / "sample.txt"
    file_path.write_text("This is a sample document for testing file organization.")
    return str(file_path)

@pytest.fixture
def api_base_url():
    """Base URL for API testing"""
    return "http://127.0.0.1:8000"