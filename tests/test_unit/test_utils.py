"""
Unit tests for utility functions and helpers
Tests decorators, validators, and utility functions
"""
import pytest
from flask import session
from decorators import admin_required, customer_required, insurer_required, regulator_required


class TestDecorators:
    """Test access control decorators"""
    
    def test_admin_required_allows_admin(self, authenticated_admin):
        """Test admin decorator allows admin users"""
        response = authenticated_admin.get('/admin/dashboard')
        assert response.status_code == 200
    
    def test_admin_required_blocks_customer(self, authenticated_customer):
        """Test admin decorator blocks customer users"""
        response = authenticated_customer.get('/admin/dashboard')
        assert response.status_code == 302  # Redirect
    
    def test_customer_required_allows_customer(self, authenticated_customer):
        """Test customer decorator allows customer users"""
        response = authenticated_customer.get('/customer/dashboard')
        assert response.status_code == 200
    
    def test_customer_required_blocks_admin(self, authenticated_admin):
        """Test customer decorator blocks admin users"""
        response = authenticated_admin.get('/customer/dashboard')
        assert response.status_code == 302  # Redirect
    
    def test_insurer_required_allows_insurer(self, authenticated_insurer):
        """Test insurer decorator allows insurer users"""
        response = authenticated_insurer.get('/insurer/dashboard')
        assert response.status_code == 200
    
    def test_regulator_required_allows_regulator(self, authenticated_regulator):
        """Test regulator decorator allows regulator users"""
        response = authenticated_regulator.get('/regulator/dashboard')
        assert response.status_code == 200


class TestFormValidation:
    """Test form validation logic"""
    
    def test_signup_form_validation(self, client):
        """Test signup form validates required fields"""
        response = client.post('/auth/signup', data={
            'username': '',
            'email': 'invalid-email',
            'password': '123',
            'user_type': 'customer'
        })
        assert response.status_code == 200  # Returns to form with errors
    
    def test_policy_creation_requires_fields(self, authenticated_insurer):
        """Test policy creation requires all fields"""
        response = authenticated_insurer.post('/insurer/create-policy', data={
            'policy_number': '',  # Missing required field
            'insured_name': 'Test User'
        })
        assert response.status_code == 200  # Returns to form


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_password_hashing(self):
        """Test password hashing works correctly"""
        from werkzeug.security import generate_password_hash, check_password_hash
        password = 'TestPassword123'
        hashed = generate_password_hash(password)
        
        assert hashed != password
        assert check_password_hash(hashed, password)
        assert not check_password_hash(hashed, 'WrongPassword')
    
    def test_file_upload_validation(self):
        """Test file upload allowed extensions"""
        from werkzeug.utils import secure_filename
        
        # Valid filenames
        assert secure_filename('photo.jpg') == 'photo.jpg'
        assert secure_filename('document.pdf') == 'document.pdf'
        
        # Invalid/dangerous filenames
        assert secure_filename('../../../etc/passwd') == 'etc_passwd'
        assert secure_filename('file with spaces.jpg') == 'file_with_spaces.jpg'
