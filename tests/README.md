# LlamaFS Test Suite

This directory contains the test suite for LlamaFS, organized following FastAPI best practices.

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and test configuration
├── README.md                   # This file
├── unit/                       # Unit tests (fast, mocked dependencies)
│   ├── __init__.py
│   ├── test_core_functionality.py    # Core LiteLLM integration tests
│   ├── test_imports.py               # Module import validation
│   └── test_watch_functionality.py   # File watching component tests
├── integration/                # Integration tests (real dependencies)
│   ├── __init__.py
│   └── test_api_models.py           # Real API calls with external services
├── system/                     # System tests (end-to-end workflows)
│   ├── __init__.py
│   └── test_full_workflows.py       # Complete FastAPI endpoint testing
└── e2e/                        # Browser-based end-to-end tests
    ├── __init__.py
    ├── conftest.py             # E2E-specific fixtures
    └── playwright.config.js    # Playwright configuration (future)
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions, classes, and methods in isolation
- **Dependencies**: Mock external services (no real API calls)
- **Speed**: Fast execution (<1s per test)
- **Markers**: `@pytest.mark.unit`
- **Run with**: `pytest -m unit`

### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions with real external dependencies
- **Dependencies**: Real Ollama server, external API keys
- **Speed**: Moderate (may take several seconds)
- **Markers**: `@pytest.mark.integration`, `@pytest.mark.slow`
- **Run with**: `pytest -m integration`

### System Tests (`tests/system/`)
- **Purpose**: End-to-end business workflows using the complete FastAPI application
- **Dependencies**: Running FastAPI server, real file system operations
- **Speed**: Slower (full request/response cycle)
- **Markers**: `@pytest.mark.system`, `@pytest.mark.slow` (for longer tests)
- **Run with**: `pytest -m system`

### E2E Tests (`tests/e2e/`)
- **Purpose**: Browser-based testing of complete user journeys
- **Dependencies**: Playwright, running application
- **Speed**: Slowest (browser automation)
- **Markers**: `@pytest.mark.e2e`
- **Run with**: `pytest -m e2e`

## Development Environment

This project uses **direnv** for automatic virtual environment activation. When you `cd` into the project directory, the venv is automatically loaded via `.envrc` (using `layout python`). 

**No need to manually run `source venv/bin/activate`** - just run commands directly.

## Running Tests

### Quick Test Commands
```bash
# Run all tests
pytest

# Run only fast tests (unit tests)
pytest -m unit

# Run tests that require external services
pytest -m integration

# Run complete workflow tests
pytest -m system

# Run tests by directory
pytest tests/unit/
pytest tests/integration/
pytest tests/system/

# Run specific test file
pytest tests/unit/test_core_functionality.py

# Skip slow tests
pytest -m "not slow"

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src
```

### Prerequisites by Test Type

1. **Unit tests**: No external dependencies
2. **Integration tests**: 
   - Local Ollama running with `llama3.2` and `moondream` models
   - Optional: API keys for cloud providers (GROQ_API_KEY, etc.)
3. **System tests**: 
   - FastAPI server running on `http://127.0.0.1:8000`
   - Start with: `fastapi dev server.py`
4. **E2E tests**: 
   - Playwright installed and configured
   - Complete application running

## File Naming Conventions

| Test Type | Prefix | Example | Description |
|-----------|--------|---------|-------------|
| Unit | `test_` | `test_core_functionality.py` | Function/class level testing |
| Integration | `test_` | `test_api_models.py` | Component integration testing |
| System | `test_` | `test_full_workflows.py` | Complete workflow testing |
| E2E | `test_` | `test_user_journeys.py` | Browser-based user flows |

## Test Markers

Tests are marked with pytest markers to enable selective execution:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (external dependencies)
- `@pytest.mark.system` - System tests (full application)
- `@pytest.mark.e2e` - End-to-end tests (browser automation)
- `@pytest.mark.slow` - Tests that take longer than 30 seconds
- `@pytest.mark.asyncio` - Async test functions

## Test Coverage Areas

- ✅ **Module imports and dependencies** (`test_imports.py`)
- ✅ **LiteLLM integration with multiple providers** (`test_core_functionality.py`)
- ✅ **File processing (text and images)** (`test_api_models.py`)
- ✅ **Watch mode file system monitoring** (`test_watch_functionality.py`)
- ✅ **FastAPI endpoint validation** (`test_full_workflows.py`)
- ✅ **File operations and error scenarios** (`test_full_workflows.py`)
- ✅ **Performance characteristics** (`test_full_workflows.py`)
- 🔄 **Browser-based user interactions** (planned for `tests/e2e/`)

## Configuration

The test suite is configured via `pytest.ini`:
- Async test support with `asyncio_mode = auto`
- Automatic test discovery in `tests/` directory
- Custom markers for test categorization
- Warning filters for cleaner output

For more details on the LlamaFS project structure and development setup, see the main project documentation.