# Unit Tests Documentation

This document provides comprehensive documentation for the unit tests implemented for the `service_router.py` functionality.

## Overview

The unit test suite provides complete coverage for the `service_router.py` module, including all endpoints, utility functions, and HTML cleaning functionality. All tests use mocking strategies to avoid actual network requests while ensuring thorough validation of the code logic.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Test configuration and fixtures
├── test_service_router.py   # Main service_router tests
├── test_utils.py            # Utils module tests
├── test_clean_html.py       # HTML cleaning functionality tests
├── pytest.ini              # Pytest configuration
└── run_tests.py            # Test execution script
```

## Test Coverage

### 1. Service Router Tests (`test_service_router.py`)

#### GET HTML Functionality
- ✅ **Successful HTML retrieval**
  - Tests successful HTML content fetching
  - Validates response format and status codes
- ✅ **Proxy usage testing**
  - Tests HTML retrieval with proxy enabled
  - Compares proxy vs non-proxy responses
- ✅ **Input validation**
  - Invalid URL handling
  - Invalid browser type validation
  - Timeout parameter validation

#### HTML Cleaning Functionality
- ✅ **Basic HTML cleaning**
  - Tests HTML content cleaning with various parsers
  - Validates cleaned output format
- ✅ **Empty input handling**
  - Tests behavior with empty HTML input

#### Browser Information Tests
- ✅ **Browser availability status**
  - Tests browser service availability checks
  - Returns appropriate status codes (200/503)
- ✅ **Supported browsers list**
  - Tests retrieval of supported browser types
  - Validates response format

#### Health Check Tests
- ✅ **Liveness probe**
  - Tests application liveness endpoint
  - Always returns "ok" status
- ✅ **Readiness probe**
  - Tests application readiness with browser availability
  - Returns appropriate status based on browser state

#### Screenshot Functionality
- ✅ **Screenshot capture**
  - Tests successful screenshot generation
  - Validates base64 encoded response
- ✅ **Input validation**
  - Tests screenshot parameters validation

### 2. ProxyManager Mock Tests

#### Proxy Retrieval Tests
- ✅ **Dynamic proxy mode**
  - Tests dynamic proxy retrieval
  - Mocks proxy API calls
- ✅ **Static proxy mode**
  - Tests static proxy configuration
  - Validates static proxy usage
- ✅ **No proxy mode**
  - Tests operation without proxy
  - Validates null proxy handling

#### Proxy Validation Tests
- ✅ **Proxy availability check**
  - Tests proxy connectivity validation
  - Mocks successful proxy checks
- ✅ **Exception handling**
  - Tests proxy check failure scenarios
  - Validates error handling

**Important**: All proxy tests use mocking and do not perform actual network requests.

### 3. Utils Module Tests (`test_utils.py`)

#### Request Management
- ✅ **Waiting requests count**
  - Tests semaphore waiter counting
  - Handles edge cases (empty/none waiters)

#### HTML Retrieval Functionality
- ✅ **Successful HTML retrieval**
  - Tests complete HTML fetching workflow
  - Validates response structure
- ✅ **Cache usage**
  - Tests cached response retrieval
  - Validates cache hit indicators
- ✅ **Timeout handling**
  - Tests page load timeout scenarios
  - Validates timeout error responses
- ✅ **Force content retrieval**
  - Tests forced content fetching on timeout
  - Validates partial content retrieval
- ✅ **Exception handling**
  - Tests general exception scenarios
  - Validates error response codes

#### Screenshot Functionality
- ✅ **Screenshot capture**
  - Tests successful screenshot generation
  - Validates base64 encoding
- ✅ **Full page screenshots**
  - Tests full page screenshot options
  - Validates screenshot parameters
- ✅ **Exception handling**
  - Tests screenshot failure scenarios
  - Validates error responses

### 4. HTML Cleaning Tests (`test_clean_html.py`)

#### Basic Cleaning Functionality
- ✅ **Script and style removal**
  - Tests removal of `<script>`, `<style>`, `<link>` tags
  - Validates content preservation
- ✅ **Media tag removal**
  - Tests removal of `<img>`, `<video>`, `<audio>`, `<canvas>` tags
  - Validates content cleanup
- ✅ **Hidden element removal**
  - Tests removal of elements with `display: none` or `visibility: hidden`
  - Validates visible content preservation

#### Advanced Cleaning Features
- ✅ **JavaScript link removal**
  - Tests removal of `javascript:` links
  - Preserves normal links
- ✅ **Attribute cleaning**
  - Tests removal of unnecessary attributes
  - Preserves important attributes (`href`, `src`, `alt`, `title`)
- ✅ **Tag unwrapping**
  - Tests unwrapping of `<div>`, `<span>`, `<input>` tags
  - Preserves content while removing wrapper tags
- ✅ **Comment handling**
  - Tests HTML comment processing
  - Validates content preservation

#### Complex Structure Handling
- ✅ **Complex HTML processing**
  - Tests cleaning of complex nested HTML structures
  - Validates comprehensive cleanup
- ✅ **Parser compatibility**
  - Tests different BeautifulSoup parsers
  - Validates parser-specific behavior

**Test Results**: All 13 HTML cleaning tests pass successfully.

### 5. Integration Tests - Request Comparison

#### Content Comparison Tests
- ✅ **HTML content comparison**
  - Compares proxy vs non-proxy HTML responses
  - Validates content differences
- ✅ **Screenshot comparison**
  - Compares different screenshot data
  - Validates screenshot variations
- ✅ **Error handling comparison**
  - Compares different error scenarios
  - Validates error type differences

## Running Tests

### Prerequisites

Ensure you have the required dependencies installed using `uv`:

```bash
uv add --dev pytest pytest-asyncio pytest-cov httpx
```

### Running All Tests

```bash
# Using uv (recommended)
uv run pytest tests/ -v

# Using pytest directly
pytest tests/ -v
```

### Running Specific Test Files

```bash
# Service router tests
uv run pytest tests/test_service_router.py -v

# Utils module tests
uv run pytest tests/test_utils.py -v

# HTML cleaning tests
uv run pytest tests/test_clean_html.py -v
```

### Running Specific Test Cases

```bash
# Run specific test class
uv run pytest tests/test_clean_html.py::TestCleanHtmlUtils -v

# Run specific test method
uv run pytest tests/test_clean_html.py::TestCleanHtmlUtils::test_clean_html_basic -v
```

### Generating Coverage Reports

```bash
# Terminal coverage report
uv run pytest tests/ --cov=apis --cov=utils --cov=base_proxy --cov-report=term-missing

# HTML coverage report
uv run pytest tests/ --cov=apis --cov=utils --cov=base_proxy --cov-report=html
```

### Using the Test Script

```bash
# Run all tests
python run_tests.py

# Run unit tests only
python run_tests.py unit

# Run specific test file
python run_tests.py test_service_router.py
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
asyncio_mode = auto
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### Test Fixtures (`conftest.py`)

The test configuration provides several key fixtures:

- **`mock_session`**: Simulates database sessions
- **`mock_proxy_manager`**: Mocks ProxyManager functionality
- **`mock_browser_manager`**: Mocks browser management
- **`mock_browser`**: Simulates browser instances and page operations
- **`client`**: FastAPI test client
- **`sample_url_input`**: Standard URL input test data
- **`sample_screenshot_input`**: Standard screenshot input test data
- **`sample_clean_html_input`**: Standard HTML cleaning input test data

## Important Notes

### Mock Strategy

1. **ProxyManager**: Completely mocked to avoid actual network requests
2. **BrowserManager**: Mocked browser instances and page operations
3. **Database Sessions**: Uses AsyncMock for database operations
4. **External Dependencies**: All external dependencies are appropriately mocked

### No Actual Network Requests

As requested, the unit tests:
- ✅ Do not perform actual website requests
- ✅ Mock ProxyManager functionality
- ✅ Test endpoint logic and response formats
- ✅ Validate error handling and edge cases

### Test Data Management

- Uses fixtures for standardized test data
- Supports different scenarios and input data
- Includes boundary conditions and exception cases

### Async Testing

- Uses `pytest-asyncio` for async test support
- Properly handles async function testing
- Maintains test isolation

## Current Design Limitations

### 1. Mock Limitations

- **Browser Behavior**: Mocked browsers may not reflect real browser quirks
- **Network Conditions**: Cannot test actual network latency or connection issues
- **Proxy Behavior**: Mocked proxy responses may not match real proxy behavior

### 2. Test Coverage Gaps

- **Integration Testing**: Limited integration testing with real services
- **Performance Testing**: No performance benchmarks or load testing
- **Browser-Specific Features**: Limited testing of browser-specific functionality

### 3. Environment Dependencies

- **Python Version**: Tests require Python 3.12+
- **Dependency Management**: Requires `uv` for dependency management
- **Test Environment**: Tests assume specific project structure

### 4. Mock Accuracy

- **Response Simulation**: Mocked responses may not match real API responses exactly
- **Error Simulation**: Mocked errors may not cover all real-world error scenarios
- **State Management**: Mocked state may not reflect real application state

## Extending Tests

### Adding New Test Cases

1. **Identify Test Scope**: Determine if it's a unit, integration, or end-to-end test
2. **Use Existing Fixtures**: Leverage existing fixtures or create new ones
3. **Follow Naming Conventions**: Use descriptive test method names
4. **Include Edge Cases**: Test both success and failure scenarios

### Example Test Structure

```python
def test_new_functionality(self, client, mock_session):
    """Test description"""
    # Arrange
    test_data = {"key": "value"}
    
    # Act
    response = client.post("/endpoint", json=test_data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["result"] == "expected"
```

### Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Use descriptive assertion messages
3. **Mock Appropriately**: Mock external dependencies, not internal logic
4. **Cover Edge Cases**: Test boundary conditions and error scenarios
5. **Maintain Test Data**: Keep test data realistic and maintainable

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed via `uv`
2. **Async Test Failures**: Check that async tests use proper decorators
3. **Mock Failures**: Verify mock configurations match actual implementations
4. **Test Isolation**: Ensure tests don't interfere with each other

### Debug Commands

```bash
# Run tests with verbose output
uv run pytest tests/ -vv

# Run tests with debug output
uv run pytest tests/ --tb=long

# Run specific failing test
uv run pytest tests/test_service_router.py::TestServiceRouter::test_get_html_success -vv
```

## Conclusion

The unit test suite provides comprehensive coverage for the `service_router.py` functionality while maintaining isolation from external dependencies. The tests validate both normal operation and error handling scenarios, ensuring robust code behavior.

For questions or issues with the tests, refer to the test code comments or the project documentation.