"""
Functional tests for navigation and UI workflows
Tests user navigation paths and page accessibility
"""
import pytest


class TestPublicNavigation:
    """Test navigation for unauthenticated users"""
    
    def test_homepage_accessible(self, client):
        """Test homepage is accessible"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'ClearView' in response.data or b'Insurance' in response.data
    
    def test_features_page_accessible(self, client):
        """Test features page is accessible"""
        response = client.get('/features')
        assert response.status_code == 200
        assert b'Features' in response.data or b'feature' in response.data.lower()
    
    def test_blog_page_accessible(self, client):
        """Test blog page is accessible"""
        response = client.get('/blog')
        assert response.status_code == 200
    
    def test_contact_page_accessible(self, client):
        """Test contact page is accessible"""
        response = client.get('/contact')
        assert response.status_code == 200
        assert b'Contact' in response.data or b'contact' in response.data.lower()
    
    def test_login_page_accessible(self, client):
        """Test login page is accessible"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_signup_page_accessible(self, client):
        """Test signup page is accessible"""
        response = client.get('/auth/signup')
        assert response.status_code == 200
        assert b'sign' in response.data.lower()


class TestAdminNavigation:
    """Test admin user navigation"""
    
    def test_admin_dashboard_loads(self, authenticated_admin):
        """Test admin dashboard loads successfully"""
        response = authenticated_admin.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'admin' in response.data.lower() or b'dashboard' in response.data.lower()
    
    def test_admin_can_access_user_management(self, authenticated_admin):
        """Test admin can access user management"""
        response = authenticated_admin.get('/admin/user-management')
        assert response.status_code == 200
    
    def test_admin_can_access_reports(self, authenticated_admin):
        """Test admin can access reports"""
        response = authenticated_admin.get('/admin/reports-and-insights')
        assert response.status_code == 200
    
    def test_admin_can_access_insurer_requests(self, authenticated_admin):
        """Test admin can view insurer requests"""
        response = authenticated_admin.get('/admin/review-insurer-requests')
        assert response.status_code == 200
    
    def test_admin_can_access_contact_messages(self, authenticated_admin):
        """Test admin can view contact messages"""
        response = authenticated_admin.get('/admin/contact-messages')
        assert response.status_code == 200


class TestCustomerNavigation:
    """Test customer user navigation"""
    
    def test_customer_dashboard_loads(self, authenticated_customer):
        """Test customer dashboard loads"""
        response = authenticated_customer.get('/customer/dashboard')
        assert response.status_code == 200
    
    def test_customer_can_access_policy_management(self, authenticated_customer):
        """Test customer can access policy management"""
        response = authenticated_customer.get('/customer/policy-management')
        assert response.status_code == 200
    
    def test_customer_can_search(self, authenticated_customer):
        """Test customer can access search"""
        response = authenticated_customer.get('/customer/search')
        assert response.status_code == 200
    
    def test_customer_can_search_policy(self, authenticated_customer):
        """Test customer can search for policies"""
        response = authenticated_customer.get('/customer/search-policy')
        assert response.status_code == 200


class TestInsurerNavigation:
    """Test insurer user navigation"""
    
    def test_insurer_dashboard_loads(self, authenticated_insurer):
        """Test insurer dashboard loads"""
        response = authenticated_insurer.get('/insurer/dashboard')
        assert response.status_code == 200
    
    def test_insurer_can_access_create_policy(self, authenticated_insurer):
        """Test insurer can access create policy page"""
        response = authenticated_insurer.get('/insurer/create-policy')
        assert response.status_code == 200
    
    def test_insurer_can_access_manage_policies(self, authenticated_insurer):
        """Test insurer can access manage policies"""
        response = authenticated_insurer.get('/insurer/manage-policies')
        assert response.status_code == 200
    
    def test_insurer_can_access_create_claim(self, authenticated_insurer):
        """Test insurer can access create claim page"""
        response = authenticated_insurer.get('/insurer/create-claim')
        assert response.status_code == 200
    
    def test_insurer_can_access_manage_claims(self, authenticated_insurer):
        """Test insurer can access manage claims"""
        response = authenticated_insurer.get('/insurer/manage-claims')
        assert response.status_code == 200
    
    def test_insurer_can_access_customer_requests(self, authenticated_insurer):
        """Test insurer can view customer requests"""
        response = authenticated_insurer.get('/insurer/customer-requests')
        assert response.status_code == 200
    
    def test_insurer_can_access_premium_calculator(self, authenticated_insurer):
        """Test insurer can access premium calculator"""
        response = authenticated_insurer.get('/insurer/premium-calculator')
        assert response.status_code == 200


class TestRegulatorNavigation:
    """Test regulator user navigation"""
    
    def test_regulator_dashboard_loads(self, authenticated_regulator):
        """Test regulator dashboard loads"""
        response = authenticated_regulator.get('/regulator/dashboard')
        assert response.status_code == 200
    
    def test_regulator_can_access_reports(self, authenticated_regulator):
        """Test regulator can access reports"""
        response = authenticated_regulator.get('/regulator/reports-and-insights')
        assert response.status_code == 200
