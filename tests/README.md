# GreenBite CMS - Test Suite Documentation

## Overview

This test suite provides comprehensive coverage for the GreenBite CMS application, including unit tests, integration tests, and system tests. The tests are organized to mirror the source code structure and use pytest as the testing framework.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── __init__.py
├── unit/                    # Unit tests for individual components
│   ├── security/
│   │   ├── test_security_utils.py      # Password hashing, validation, JWT
│   │   └── test_decorators.py          # Authentication decorators
│   ├── objs/
│   │   ├── test_event.py               # Event model tests
│   │   └── user/
│   │       └── test_users.py           # User model tests
│   └── services/
│       ├── test_auth_service.py        # Authentication service
│       ├── test_event_service.py       # Event service
│       └── test_admin_planner_service.py # Admin & Planner services
├── integration/             # Integration tests for component interactions
│   └── test_workflows.py               # Complete workflow tests
└── system/                  # End-to-end system tests
    └── test_api_endpoints.py           # REST API endpoint tests
```

## Installation

### 1. Install Test Dependencies

```bash
pip install -r test_requirements.txt
```

This installs:
- pytest and plugins
- pytest-cov for coverage reporting
- pytest-mock for mocking
- flask-testing for Flask app testing
- Additional test utilities

### 2. Verify Installation

```bash
pytest --version
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# System tests only
pytest -m system
```

### Run Tests by Directory

```bash
# All unit tests
pytest tests/unit/

# Security tests only
pytest tests/unit/security/

# Service tests only
pytest tests/unit/services/

# Integration tests
pytest tests/integration/

# System/API tests
pytest tests/system/
```

### Run Specific Test File

```bash
pytest tests/unit/security/test_security_utils.py
```

### Run Specific Test Class or Method

```bash
# Run specific test class
pytest tests/unit/security/test_security_utils.py::TestPasswordHasher

# Run specific test method
pytest tests/unit/security/test_security_utils.py::TestPasswordHasher::test_hash_password
```

## Coverage Reports

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=src --cov=auth_server

# With HTML report
pytest --cov=src --cov=auth_server --cov-report=html

# With terminal report
pytest --cov=src --cov=auth_server --cov-report=term-missing
```

### View HTML Coverage Report

After running with `--cov-report=html`, open:
```
htmlcov/index.html
```

### Coverage Summary

The test suite aims for minimum 80% code coverage:
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **System Tests**: Test complete workflows

## Test Output Options

### Verbose Output

```bash
pytest -v
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Run Tests in Parallel

```bash
pytest -n auto
```

## Test Markers

Tests are marked with custom markers for easy filtering:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.system` - System tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.database` - Tests requiring database

### Filter by Marker

```bash
# Run only fast tests (exclude slow)
pytest -m "not slow"

# Run database tests
pytest -m database

# Combine markers
pytest -m "unit and not slow"
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

### Database Fixtures
- `test_db_engine` - In-memory SQLite database
- `db_session` - Database session for tests

### User Fixtures
- `sample_client` - Pre-created client user
- `sample_planner` - Pre-created planner user
- `sample_admin` - Pre-created admin user

### Event Fixtures
- `sample_event` - Pre-created test event

### Token Fixtures
- `valid_token` - Valid JWT token
- `admin_token` - Admin JWT token
- `planner_token` - Planner JWT token
- `expired_token` - Expired JWT token

### Flask Fixtures
- `flask_app` - Flask application instance
- `flask_client` - Flask test client

### Example Usage

```python
def test_something(db_session, sample_client, sample_event):
    # Use fixtures in your test
    assert sample_client.id is not None
    assert sample_event.client_id == sample_client.id
```

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for MyComponent
"""
import pytest
from src.module import MyComponent


class TestMyComponent:
    """Test suite for MyComponent."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        component = MyComponent()
        result = component.do_something()
        assert result is not None
    
    def test_edge_case(self):
        """Test edge case."""
        component = MyComponent()
        with pytest.raises(ValueError):
            component.do_something_invalid()
```

### Integration Test Template

```python
"""
Integration tests for MyWorkflow
"""
import pytest


class TestMyWorkflow:
    """Test complete workflow."""
    
    def test_complete_workflow(self, db_session):
        """Test end-to-end workflow."""
        # Setup
        # ... create necessary objects
        
        # Execute workflow
        # ... perform operations
        
        # Verify
        # ... check results
        assert expected == actual
```

## Test Coverage by Component

### Security Module
- ✅ Password hashing and verification
- ✅ Input validation (email, username, password, role)
- ✅ JWT token generation and verification
- ✅ Authentication decorators
- ✅ Authorization decorators
- ✅ Security logging

### Database Models
- ✅ User models (CMSUser, Client, Planner, Admin)
- ✅ Event model
- ✅ User-Event relationships
- ✅ Planner-Event associations

### Services
- ✅ AuthService (registration, login, email check)
- ✅ EventService (create, retrieve, cancel)
- ✅ AdminService (assign planners, manage events)
- ✅ PlannerService (accept/decline events)

### API Endpoints
- ✅ Health check
- ✅ User registration
- ✅ User login
- ✅ Email checking
- ✅ Client endpoints (events, create, cancel)
- ✅ Planner endpoints (events, accept, decline)
- ✅ Admin endpoints (all events, assign planners)
- ✅ Security headers
- ✅ Rate limiting

### Workflows
- ✅ Complete event lifecycle
- ✅ Event decline workflow
- ✅ Event cancellation
- ✅ Multiple planner assignments
- ✅ Authentication flow
- ✅ Data consistency

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r Requirements.txt
        pip install -r test_requirements.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov=auth_server --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Debugging Tests

### Run with Python Debugger

```bash
pytest --pdb
```

This drops into debugger on failures.

### Print Test Output

```bash
pytest -s -v
```

### Run Single Test with Debug

```python
# In your test file
def test_something():
    import pdb; pdb.set_trace()
    # Your test code
```

## Best Practices

1. **Test Naming**: Use descriptive names starting with `test_`
2. **One Assertion Focus**: Each test should focus on one behavior
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Fixtures**: Reuse common setup code
5. **Mock External Dependencies**: Don't depend on external services
6. **Test Edge Cases**: Test boundary conditions and error cases
7. **Keep Tests Fast**: Use in-memory databases, mock slow operations
8. **Clean Up**: Tests should not leave side effects

## Common Issues and Solutions

### Issue: Import Errors

**Solution**: Ensure pytest.ini has correct pythonpath:
```ini
[pytest]
pythonpath = .
```

### Issue: Database Conflicts

**Solution**: Use in-memory database (already configured in conftest.py)

### Issue: Slow Tests

**Solution**: Run in parallel:
```bash
pytest -n auto
```

### Issue: Flaky Tests

**Solution**: Look for:
- Race conditions
- Time-dependent tests
- Unclean state between tests

## Performance

Current test execution time (approximate):
- **Unit tests**: ~2-5 seconds
- **Integration tests**: ~5-10 seconds
- **System tests**: ~10-15 seconds
- **Total**: ~20-30 seconds

## Test Metrics

Target metrics:
- **Coverage**: ≥80%
- **Pass Rate**: 100%
- **Execution Time**: <60 seconds
- **Test Count**: 150+ tests

## Contributing

When adding new features:

1. Write unit tests for new functions/classes
2. Write integration tests for workflows
3. Write system tests for API endpoints
4. Ensure coverage remains above 80%
5. Run full test suite before committing

## Support

For questions or issues with tests:
1. Check this README
2. Review conftest.py for available fixtures
3. Look at existing tests for examples
4. Check pytest documentation: https://docs.pytest.org/

## License

Same as main project.
