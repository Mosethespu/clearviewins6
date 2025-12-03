"""
Integration tests for RBAC (Role-Based Access Control)
Tests permissions and access restrictions across user roles
"""
import pytest
from extension import db
from models import InsurerRequest, RegulatorRequest


class TestInsurerApprovalWorkflow:
    """Test insurer approval and access request workflow"""
    
    def test_insurer_requests_access(self, client, app):
        """Test insurer can request access"""
        with app.app_context():
            from models import Insurer, InsuranceCompany
            company = InsuranceCompany.query.first()
            
            # Create unapproved insurer
            insurer = Insurer(
                username='pendinginsurer',
                email='pending@test.com',
                password='hashed_password',
                insurance_company_id=company.id,
                is_approved=False
            )
            db.session.add(insurer)
            db.session.commit()
        
        # Login as unapproved insurer
        client.post('/auth/login', data={
            'email': 'pending@test.com',
            'password': 'TestPassword123'
        })
        
        # Should redirect to request access
        response = client.get('/insurer/dashboard', follow_redirects=True)
        assert response.status_code == 200
    
    def test_admin_can_approve_insurer(self, authenticated_admin, app):
        """Test admin can approve insurer requests"""
        with app.app_context():
            from models import Insurer, InsuranceCompany
            company = InsuranceCompany.query.first()
            
            # Create insurer and request
            insurer = Insurer(
                username='toapprove',
                email='toapprove@test.com',
                password='hashed_password',
                insurance_company_id=company.id,
                is_approved=False
            )
            db.session.add(insurer)
            db.session.commit()
            
            request = InsurerRequest(
                insurer_id=insurer.id,
                reason='Need access to manage policies',
                status='pending'
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Admin approves request
        response = authenticated_admin.post(f'/admin/approve-insurer/{request_id}', 
                                           follow_redirects=True)
        assert response.status_code == 200
        
        # Verify insurer is approved
        with app.app_context():
            insurer = Insurer.query.filter_by(email='toapprove@test.com').first()
            assert insurer.is_approved is True


class TestRegulatorApprovalWorkflow:
    """Test regulator approval workflow"""
    
    def test_admin_can_approve_regulator(self, authenticated_admin, app):
        """Test admin can approve regulator requests"""
        with app.app_context():
            from models import Regulator, RegulatoryBody
            reg_body = RegulatoryBody.query.first()
            
            # Create regulator and request
            regulator = Regulator(
                username='pendingregulator',
                email='pendingreg@test.com',
                password='hashed_password',
                regulatory_body_id=reg_body.id,
                is_approved=False
            )
            db.session.add(regulator)
            db.session.commit()
            
            request = RegulatorRequest(
                regulator_id=regulator.id,
                reason='Need regulatory oversight access',
                status='pending'
            )
            db.session.add(request)
            db.session.commit()
            request_id = request.id
        
        # Admin approves
        response = authenticated_admin.post(f'/admin/approve-regulator/{request_id}',
                                           follow_redirects=True)
        assert response.status_code == 200


class TestPolicyAccessControl:
    """Test policy access control across roles"""
    
    def test_insurer_can_create_policy(self, authenticated_insurer, app):
        """Test insurer can create policies"""
        response = authenticated_insurer.get('/insurer/create-policy')
        assert response.status_code == 200
    
    def test_customer_cannot_create_policy(self, authenticated_customer):
        """Test customer cannot create policies"""
        response = authenticated_customer.get('/insurer/create-policy')
        assert response.status_code == 302  # Redirected
    
    def test_customer_can_view_own_policies(self, authenticated_customer, app):
        """Test customer can view their own policies"""
        response = authenticated_customer.get('/customer/policy-management')
        assert response.status_code == 200
    
    def test_regulator_can_view_all_policies(self, authenticated_regulator):
        """Test regulator can view all policies"""
        response = authenticated_regulator.get('/regulator/dashboard')
        assert response.status_code == 200


class TestClaimAccessControl:
    """Test claim access control"""
    
    def test_insurer_can_create_claim(self, authenticated_insurer):
        """Test insurer can create claims"""
        response = authenticated_insurer.get('/insurer/create-claim')
        assert response.status_code == 200
    
    def test_customer_can_view_own_claims(self, authenticated_customer):
        """Test customer can view their own claims"""
        response = authenticated_customer.get('/customer/dashboard')
        assert response.status_code == 200
