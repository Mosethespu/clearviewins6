"""
Configuration file for pytest
Sets up test environment and fixtures
"""
import pytest
import os
import tempfile
from app import app as flask_app
from extension import db
from models import Admin, Customer, Insurer, Regulator, InsuranceCompany, RegulatoryBody
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create application instance for testing"""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key',
    })
    
    # Create database tables
    with flask_app.app_context():
        db.create_all()
        
        # Create test insurance company
        test_company = InsuranceCompany(name="Test Insurance Co", is_active=True)
        db.session.add(test_company)
        
        # Create test regulatory body
        test_reg_body = RegulatoryBody(name="Test Regulatory Body", is_active=True)
        db.session.add(test_reg_body)
        db.session.commit()
    
    yield flask_app
    
    # Cleanup
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    """Create test admin user"""
    with app.app_context():
        admin = Admin(
            username='testadmin',
            email='admin@test.com',
            password=generate_password_hash('TestPassword123'),
            staff_id='ADM001',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def customer_user(app):
    """Create test customer user"""
    with app.app_context():
        customer = Customer(
            username='testcustomer',
            email='customer@test.com',
            password=generate_password_hash('TestPassword123'),
            is_active=True
        )
        db.session.add(customer)
        db.session.commit()
        return customer


@pytest.fixture
def insurer_user(app):
    """Create test insurer user"""
    with app.app_context():
        company = InsuranceCompany.query.first()
        insurer = Insurer(
            username='testinsurer',
            email='insurer@test.com',
            password=generate_password_hash('TestPassword123'),
            staff_id='INS001',
            insurance_company_id=company.id,
            is_approved=True,
            is_active=True
        )
        db.session.add(insurer)
        db.session.commit()
        return insurer


@pytest.fixture
def regulator_user(app):
    """Create test regulator user"""
    with app.app_context():
        reg_body = RegulatoryBody.query.first()
        regulator = Regulator(
            username='testregulator',
            email='regulator@test.com',
            password=generate_password_hash('TestPassword123'),
            staff_id='REG001',
            regulatory_body_id=reg_body.id,
            is_approved=True,
            is_active=True
        )
        db.session.add(regulator)
        db.session.commit()
        return regulator


@pytest.fixture
def authenticated_admin(client, admin_user):
    """Login as admin and return client"""
    client.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'TestPassword123'
    }, follow_redirects=True)
    return client


@pytest.fixture
def authenticated_customer(client, customer_user):
    """Login as customer and return client"""
    client.post('/auth/login', data={
        'email': 'customer@test.com',
        'password': 'TestPassword123'
    }, follow_redirects=True)
    return client


@pytest.fixture
def authenticated_insurer(client, insurer_user):
    """Login as insurer and return client"""
    client.post('/auth/login', data={
        'email': 'insurer@test.com',
        'password': 'TestPassword123'
    }, follow_redirects=True)
    return client


@pytest.fixture
def authenticated_regulator(client, regulator_user):
    """Login as regulator and return client"""
    client.post('/auth/login', data={
        'email': 'regulator@test.com',
        'password': 'TestPassword123'
    }, follow_redirects=True)
    return client
