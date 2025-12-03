"""
Integration tests for authentication and authorization
Tests login, logout, signup, and access control flows
"""
import pytest
from flask import session


class TestAuthenticationFlow:
    """Test complete authentication workflows"""
    
    def test_signup_and_login_customer(self, client, app):
        """Test customer can sign up and login"""
        # Sign up
        response = client.post('/auth/signup', data={
            'username': 'newcustomer',
            'email': 'newcustomer@test.com',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'user_type': 'customer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Login
        response = client.post('/auth/login', data={
            'email': 'newcustomer@test.com',
            'password': 'Password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'customer' in response.data.lower() or b'dashboard' in response.data.lower()
    
    def test_signup_duplicate_email_fails(self, client, customer_user):
        """Test signup fails with duplicate email"""
        response = client.post('/auth/signup', data={
            'username': 'duplicate',
            'email': 'customer@test.com',  # Already exists
            'password': 'Password123',
            'confirm_password': 'Password123',
            'user_type': 'customer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'already' in response.data.lower() or b'exists' in response.data.lower()
    
    def test_login_wrong_password_fails(self, client, customer_user):
        """Test login fails with wrong password"""
        response = client.post('/auth/login', data={
            'email': 'customer@test.com',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'invalid' in response.data.lower() or b'incorrect' in response.data.lower()
    
    def test_logout(self, authenticated_customer):
        """Test logout functionality"""
        response = authenticated_customer.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Try to access protected page after logout
        response = authenticated_customer.get('/customer/dashboard')
        assert response.status_code == 302  # Redirected to login


class TestRoleBasedAccessControl:
    """Test RBAC across different user types"""
    
    def test_admin_can_access_admin_dashboard(self, authenticated_admin):
        """Test admin can access admin dashboard"""
        response = authenticated_admin.get('/admin/dashboard')
        assert response.status_code == 200
    
    def test_admin_cannot_access_customer_dashboard(self, authenticated_admin):
        """Test admin cannot access customer dashboard"""
        response = authenticated_admin.get('/customer/dashboard')
        assert response.status_code == 302
    
    def test_customer_can_access_customer_dashboard(self, authenticated_customer):
        """Test customer can access customer dashboard"""
        response = authenticated_customer.get('/customer/dashboard')
        assert response.status_code == 200
    
    def test_customer_cannot_access_admin_dashboard(self, authenticated_customer):
        """Test customer cannot access admin dashboard"""
        response = authenticated_customer.get('/admin/dashboard')
        assert response.status_code == 302
    
    def test_insurer_can_access_insurer_dashboard(self, authenticated_insurer):
        """Test insurer can access insurer dashboard"""
        response = authenticated_insurer.get('/insurer/dashboard')
        assert response.status_code == 200
    
    def test_insurer_cannot_access_regulator_dashboard(self, authenticated_insurer):
        """Test insurer cannot access regulator dashboard"""
        response = authenticated_insurer.get('/regulator/dashboard')
        assert response.status_code == 302
    
    def test_regulator_can_access_regulator_dashboard(self, authenticated_regulator):
        """Test regulator can access regulator dashboard"""
        response = authenticated_regulator.get('/regulator/dashboard')
        assert response.status_code == 200
    
    def test_unauthenticated_redirected_to_login(self, client):
        """Test unauthenticated users are redirected to login"""
        response = client.get('/customer/dashboard')
        assert response.status_code == 302
        assert b'/auth/login' in response.data or response.location.endswith('/auth/login')
