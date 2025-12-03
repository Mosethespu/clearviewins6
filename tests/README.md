# ClearView Insurance Test Suite

This directory contains comprehensive tests for the ClearView Insurance application. The test suite follows industry best practices with organized test categories covering unit, integration, functional, end-to-end, and performance testing.

## Table of Contents

- [Test Structure](#test-structure)
- [Setup Requirements](#setup-requirements)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Fixtures](#fixtures)
- [Adding New Tests](#adding-new-tests)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)

## Test Structure

```
tests/
├── __init__.py                           # Package initialization
├── conftest.py                           # Pytest configuration and shared fixtures
├── README.md                             # This file
├── test_unit/                            # Unit tests (isolated component testing)
│   ├── test_models.py                    # Database model tests
│   └── test_utils.py                     # Utility function tests
├── test_integration/                     # Integration tests (component interaction)
│   ├── test_auth_flow.py                 # Authentication workflow tests
│   └── test_rbac.py                      # Role-based access control tests
├── test_functional/                      # Functional tests (feature testing)
│   ├── test_navigation.py                # Navigation and routing tests
│   └── test_forms.py                     # Form submission and validation tests
├── test_e2e/                             # End-to-end tests (complete workflows)
│   └── test_full_workflow.py             # Complete user journey tests
└── test_performance/                     # Performance tests (load and speed)
    └── locustfile.py                     # Performance and load tests
```

## Setup Requirements

### 1. Install Test Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install pytest and related packages
pip install pytest pytest-flask pytest-cov

# For coverage reporting
pip install coverage
```

### 2. Environment Setup

The test suite uses an isolated SQLite database (`test.db`) that is created and destroyed for each test session. No additional configuration is needed.

## Running Tests

### Run All Tests

```bash
# Run entire test suite
pytest

# Run with verbose output
pytest -v

# Run with detailed output
pytest -vv
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_unit/

# Integration tests only
pytest tests/test_integration/

# Functional tests only
pytest tests/test_functional/

# End-to-end tests only
pytest tests/test_e2e/

# Performance tests only
pytest tests/test_performance/
```

### Run Specific Test Files

```bash
# Run model tests
pytest tests/test_unit/test_models.py

# Run authentication tests
pytest tests/test_integration/test_auth_flow.py

# Run navigation tests
pytest tests/test_functional/test_navigation.py
```

### Run Specific Test Classes or Methods

```bash
# Run specific test class
pytest tests/test_unit/test_models.py::TestPolicyModel

# Run specific test method
pytest tests/test_unit/test_models.py::TestPolicyModel::test_create_policy

# Run tests matching a keyword
pytest -k "login"
```

### Run Tests with Coverage

```bash
# Run with coverage report
pytest --cov=. --cov-report=html

# Run with terminal coverage report
pytest --cov=. --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Categories

### 1. Unit Tests (`test_unit/`)

**Purpose:** Test individual components in isolation without dependencies.

- **`test_models.py`** - Database model tests
  - Model creation and validation
  - Password hashing verification
  - Relationship testing (policies, claims, photos)
  - Default value checks
  - Coverage: Admin, Customer, Insurer, Regulator, Policy, Claim, BlogPost, ContactMessage models

- **`test_utils.py`** - Utility function tests
  - Decorator access control (@admin_required, @customer_required, etc.)
  - Form validation functions
  - Password hashing and verification
  - File upload validation
  - Secure filename handling

**Example:**
```python
def test_create_admin(self, app):
    """Test creating an admin user"""
    with app.app_context():
        admin = Admin(
            username='testadmin',
            email='admin@test.com',
            password='HashedPassword123'
        )
        db.session.add(admin)
        db.session.commit()
        
        saved_admin = Admin.query.filter_by(email='admin@test.com').first()
        assert saved_admin is not None
        assert saved_admin.username == 'testadmin'
```

### 2. Integration Tests (`test_integration/`)

**Purpose:** Test how components work together, including database interactions.

- **`test_auth_flow.py`** - Authentication workflow tests
  - Signup and login flow
  - Duplicate email prevention
  - Wrong password handling
  - Logout and session clearing

- **`test_rbac.py`** - Role-based access control tests
  - Insurer approval workflow (pending → approved)
  - Regulator approval workflow
  - Policy access control (insurer creates, customer views own, regulator views all)
  - Claim access control

**Example:**
```python
def test_insurer_approval_workflow(self, client, app):
    """Test complete insurer approval flow"""
    # Create pending insurer
    with app.app_context():
        insurer = Insurer(
            username='testinsurer',
            email='insurer@test.com',
            password=generate_password_hash('Password123'),
            insurance_company_id='IC001',
            is_approved=False
        )
        db.session.add(insurer)
        db.session.commit()
    
    # Admin approves
    with app.app_context():
        insurer = Insurer.query.filter_by(email='insurer@test.com').first()
        insurer.is_approved = True
        db.session.commit()
    
    # Verify approval
    with app.app_context():
        insurer = Insurer.query.filter_by(email='insurer@test.com').first()
        assert insurer.is_approved is True
```

### 3. Functional Tests (`test_functional/`)

**Purpose:** Test complete features from a user perspective.

- **`test_navigation.py`** - Navigation and routing tests
  - Public pages (homepage, features, blog, contact)
  - Admin navigation (dashboard, user management, reports, contact messages)
  - Customer navigation (dashboard, policy management, search)
  - Insurer navigation (dashboard, policy/claim management, customer requests)
  - Regulator navigation (dashboard, reports)

- **`test_forms.py`** - Form submission and validation tests
  - Contact form submission and validation
  - Policy creation with valid data
  - Claim creation validation
  - Policy search functionality

**Example:**
```python
def test_contact_form_submission(self, client):
    """Test contact form submission"""
    response = client.post('/contact', data={
        'name': 'John Doe',
        'email': 'john@test.com',
        'message': 'Test message'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify message saved to database
    with app.app_context():
        message = ContactMessage.query.filter_by(email='john@test.com').first()
        assert message is not None
        assert message.name == 'John Doe'
```

### 4. End-to-End Tests (`test_e2e/`)

**Purpose:** Test complete user workflows from start to finish.

- **`test_full_workflow.py`** - Complete user journey tests
  - **Customer workflow:** Signup → Login → Policy Search
  - **Insurer workflow:** Login → Create Policy → Create Claim
  - **Policy request cycle:** Customer requests access → Insurer approves → Policy email updated

**Example:**
```python
def test_complete_customer_workflow(self, client, app):
    """Test complete customer journey"""
    # Step 1: Signup
    response = client.post('/auth/signup', data={
        'username': 'newcustomer',
        'email': 'newcustomer@test.com',
        'password': 'Password123',
        'confirm_password': 'Password123',
        'user_type': 'customer'
    })
    
    # Step 2: Activate and login
    with app.app_context():
        customer = Customer.query.filter_by(email='newcustomer@test.com').first()
        customer.is_active = True
        db.session.commit()
    
    response = client.post('/auth/login', data={
        'email': 'newcustomer@test.com',
        'password': 'Password123'
    })
    
    # Step 3: Search for policies
    response = client.get('/customer/search?policy_number=POL-001')
    assert response.status_code == 200
```

### 5. Performance Tests (`test_performance/`)

**Purpose:** Test application performance under various load conditions.

- **`locustfile.py`** - Performance and load tests
  - Response time tests (homepage, login, dashboard)
  - Database query performance
  - Concurrent request handling
  - Memory usage patterns
  - Bulk data operations

**Example:**
```python
def test_homepage_response_time(self, client):
    """Test homepage loads within acceptable time"""
    start_time = time.time()
    response = client.get('/')
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response.status_code == 200
    assert response_time < 2.0  # Should load in less than 2 seconds
```

## Fixtures

Fixtures are defined in `conftest.py` and provide reusable test setup.

### Available Fixtures

#### Core Fixtures

- **`app`** - Flask application instance with test configuration
  ```python
  @pytest.fixture
  def app():
      """Create and configure a new app instance for each test"""
      app = create_app()
      app.config['TESTING'] = True
      app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
      # ... returns configured app
  ```

- **`client`** - Test client for making HTTP requests
  ```python
  def test_homepage(client):
      response = client.get('/')
      assert response.status_code == 200
  ```

#### User Fixtures

- **`admin_user`** - Admin user in database
- **`customer_user`** - Customer user in database
- **`insurer_user`** - Insurer user in database (approved)
- **`regulator_user`** - Regulator user in database (approved)

#### Authenticated Client Fixtures

- **`authenticated_admin`** - Test client logged in as admin
- **`authenticated_customer`** - Test client logged in as customer
- **`authenticated_insurer`** - Test client logged in as insurer
- **`authenticated_regulator`** - Test client logged in as regulator

**Usage Example:**
```python
def test_admin_dashboard(authenticated_admin):
    """Test admin can access dashboard"""
    response = authenticated_admin.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data
```

#### Policy and Claim Fixtures

- **`policy`** - Sample policy in database
- **`claim`** - Sample claim in database

## Adding New Tests

### 1. Choose the Right Category

- **Unit Test:** Testing a single function/method in isolation → `test_unit/`
- **Integration Test:** Testing how components work together → `test_integration/`
- **Functional Test:** Testing a complete feature → `test_functional/`
- **E2E Test:** Testing a complete user workflow → `test_e2e/`
- **Performance Test:** Testing speed/load → `test_performance/`

### 2. Create Test File

Create a new file or add to existing file:

```python
# tests/test_unit/test_my_feature.py
import pytest
from models import MyModel

class TestMyFeature:
    """Test my new feature"""
    
    def test_feature_works(self, app):
        """Test that feature works as expected"""
        with app.app_context():
            # Test implementation
            result = MyModel.do_something()
            assert result is not None
```

### 3. Use Fixtures

Leverage existing fixtures from `conftest.py`:

```python
def test_with_authenticated_user(authenticated_customer):
    """Test requires authenticated user"""
    response = authenticated_customer.get('/customer/dashboard')
    assert response.status_code == 200
```

### 4. Follow Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names that explain what is being tested

### 5. Use AAA Pattern

Structure tests with Arrange, Act, Assert:

```python
def test_create_policy(self, authenticated_insurer, app):
    """Test policy creation"""
    # Arrange
    policy_data = {
        'policy_number': 'POL-123',
        'insured_name': 'John Doe',
        'email_address': 'john@test.com'
    }
    
    # Act
    response = authenticated_insurer.post('/insurer/create-policy', data=policy_data)
    
    # Assert
    assert response.status_code == 302
    with app.app_context():
        policy = Policy.query.filter_by(policy_number='POL-123').first()
        assert policy is not None
        assert policy.insured_name == 'John Doe'
```

## Coverage Reports

### Generate Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open coverage report
xdg-open htmlcov/index.html
```

### Coverage Goals

- **Overall Coverage:** Target 80%+ coverage
- **Critical Paths:** 95%+ coverage for authentication, authorization, and payment flows
- **Models:** 90%+ coverage for all database models
- **Routes:** 85%+ coverage for all route handlers

### Viewing Coverage

The HTML report shows:
- Overall coverage percentage
- File-by-file coverage breakdown
- Line-by-line highlighting of covered/uncovered code
- Branch coverage information

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/tests.yml
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
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-flask pytest-cov
    
    - name: Run tests with coverage
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v2
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run tests before commit
pytest tests/test_unit/ tests/test_integration/
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Troubleshooting

### Tests Failing with Database Errors

**Solution:** Ensure test database is properly isolated:
```python
# In conftest.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
```

### Import Errors

**Solution:** Ensure `__init__.py` exists in test directories and Python path is correct:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/clearviewins6"
pytest
```

### Fixture Not Found

**Solution:** Check that fixtures are defined in `conftest.py` or imported correctly.

### Tests Pass Individually but Fail Together

**Solution:** Tests may have shared state. Ensure each test is isolated:
- Use fresh database for each test
- Clear session data between tests
- Reset global state

## Best Practices

1. **Keep Tests Independent:** Each test should be able to run in isolation
2. **Use Fixtures:** Leverage fixtures for common setup to reduce duplication
3. **Test Edge Cases:** Include tests for error conditions and boundary values
4. **Clear Test Names:** Use descriptive names that explain what is being tested
5. **Fast Tests:** Keep unit tests fast; save slow tests for integration/e2e
6. **Clean Up:** Ensure tests clean up resources (fixtures handle this automatically)
7. **Assert Specificity:** Use specific assertions rather than generic ones
8. **Documentation:** Add docstrings to explain complex test scenarios

## Test Maintenance

### Running Tests Regularly

- Run unit tests during development: `pytest tests/test_unit/`
- Run full suite before commits: `pytest`
- Run performance tests periodically: `pytest tests/test_performance/`

### Updating Tests

When modifying code:
1. Update affected tests first (TDD approach)
2. Run relevant test category
3. Run full test suite before merging
4. Update test documentation if test structure changes

### Monitoring Coverage

Regularly check coverage reports:
```bash
pytest --cov=. --cov-report=term-missing
```

Look for:
- Uncovered lines in critical paths
- Decreasing coverage trends
- Missing tests for new features

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-flask Documentation](https://pytest-flask.readthedocs.io/)
- [Flask Testing Documentation](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Support

For questions or issues with tests:
1. Check this documentation
2. Review existing test examples
3. Consult pytest documentation
4. Ask the development team

---

**Last Updated:** 2024
**Test Framework:** pytest 7.4+
**Python Version:** 3.13+
