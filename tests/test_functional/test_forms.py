"""
Functional tests for forms
Tests form submission, validation, and data processing
"""
import pytest
from extension import db


class TestContactForm:
    """Test contact form submission"""
    
    def test_contact_form_submission(self, client, app):
        """Test contact form submits successfully"""
        response = client.post('/contact', data={
            'name': 'Test User',
            'email': 'testuser@example.com',
            'message': 'This is a test message'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify message was saved
        with app.app_context():
            from models import ContactMessage
            message = ContactMessage.query.filter_by(email='testuser@example.com').first()
            assert message is not None
            assert message.name == 'Test User'
            assert message.read is False
    
    def test_contact_form_validation(self, client):
        """Test contact form validates required fields"""
        response = client.post('/contact', data={
            'name': '',
            'email': '',
            'message': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'fill' in response.data.lower() or b'required' in response.data.lower()


class TestPolicyCreationForm:
    """Test policy creation form"""
    
    def test_policy_creation_with_valid_data(self, authenticated_insurer, app):
        """Test creating a policy with valid data"""
        from datetime import datetime, timedelta
        
        response = authenticated_insurer.post('/insurer/create-policy', data={
            'policy_number': 'TEST-POL-001',
            'insured_name': 'John Doe',
            'email_address': 'john@example.com',
            'phone_number': '0712345678',
            'registration_number': 'KAA123A',
            'chassis_number': 'CH123456789',
            'make_model': 'Toyota Corolla',
            'vehicle_make': 'Toyota',
            'vehicle_model': 'Corolla',
            'year_of_manufacture': '2020',
            'policy_type': 'Comprehensive',
            'effective_date': datetime.now().strftime('%Y-%m-%d'),
            'expiry_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'premium_amount': '50000',
            'sum_insured': '2000000'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify policy was created
        with app.app_context():
            from models import Policy
            policy = Policy.query.filter_by(policy_number='TEST-POL-001').first()
            assert policy is not None
            assert policy.insured_name == 'John Doe'


class TestClaimCreationForm:
    """Test claim creation form"""
    
    def test_claim_requires_policy(self, authenticated_insurer, app):
        """Test claim creation requires valid policy"""
        with app.app_context():
            from models import Policy, Insurer
            insurer = Insurer.query.filter_by(email='insurer@test.com').first()
            
            # Create test policy
            policy = Policy(
                policy_number='POL-FOR-CLAIM',
                insured_name='Test User',
                email_address='test@example.com',
                registration_number='KBB123B',
                insurance_company_id=insurer.insurance_company_id,
                entered_by=insurer.id
            )
            db.session.add(policy)
            db.session.commit()
            policy_id = policy.id
        
        # Create claim
        from datetime import datetime
        response = authenticated_insurer.post('/insurer/create-claim', data={
            'policy_id': policy_id,
            'accident_date': datetime.now().strftime('%Y-%m-%d'),
            'accident_location': 'Nairobi CBD',
            'accident_description': 'Minor collision',
            'police_report_number': 'PR123456',
            'estimated_loss': '50000'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestPolicySearchForm:
    """Test policy search functionality"""
    
    def test_customer_can_search_policy(self, authenticated_customer, app):
        """Test customer can search for policies"""
        with app.app_context():
            from models import Policy, Insurer
            insurer = Insurer.query.filter_by(email='insurer@test.com').first()
            
            # Create searchable policy
            policy = Policy(
                policy_number='SEARCH-001',
                insured_name='Search Test',
                email_address='search@example.com',
                registration_number='KCC123C',
                insurance_company_id=insurer.insurance_company_id,
                entered_by=insurer.id
            )
            db.session.add(policy)
            db.session.commit()
        
        # Search for policy
        response = authenticated_customer.post('/customer/search-policy', data={
            'policy_number': 'SEARCH-001'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'SEARCH-001' in response.data or b'Search Test' in response.data
