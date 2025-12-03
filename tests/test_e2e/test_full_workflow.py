"""
End-to-End tests for complete user workflows
Tests full scenarios from start to finish
"""
import pytest
from extension import db
from datetime import datetime, timedelta


class TestCompleteCustomerWorkflow:
    """Test complete customer workflow from signup to policy management"""
    
    def test_customer_complete_journey(self, client, app):
        """Test customer signup, login, search, and request policy access"""
        
        # Step 1: Customer signs up
        response = client.post('/auth/signup', data={
            'username': 'newcustomer',
            'email': 'newcustomer@example.com',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'user_type': 'customer'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 2: Customer logs in
        response = client.post('/auth/login', data={
            'email': 'newcustomer@example.com',
            'password': 'Password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 3: Create a policy for customer to find
        with app.app_context():
            from models import Policy, Insurer
            insurer = Insurer.query.first()
            if insurer:
                policy = Policy(
                    policy_number='CUST-WORKFLOW-001',
                    insured_name='New Customer',
                    email_address='newcustomer@example.com',
                    registration_number='KDD123D',
                    insurance_company_id=insurer.insurance_company_id,
                    entered_by=insurer.id,
                    effective_date=datetime.now().date(),
                    expiry_date=(datetime.now() + timedelta(days=365)).date(),
                    status='Active'
                )
                db.session.add(policy)
                db.session.commit()
        
        # Step 4: Customer navigates to policy management
        response = client.get('/customer/policy-management')
        assert response.status_code == 200
        
        # Step 5: Customer searches for policy
        response = client.get('/customer/search-policy')
        assert response.status_code == 200


class TestCompleteInsurerWorkflow:
    """Test complete insurer workflow"""
    
    def test_insurer_policy_and_claim_creation(self, client, app):
        """Test insurer creates policy and claim"""
        
        # Setup: Create approved insurer
        with app.app_context():
            from models import Insurer, InsuranceCompany
            from werkzeug.security import generate_password_hash
            
            company = InsuranceCompany.query.first()
            insurer = Insurer(
                username='workflowinsurer',
                email='workflowinsurer@test.com',
                password=generate_password_hash('Password123'),
                staff_id='WF001',
                insurance_company_id=company.id,
                is_approved=True,
                is_active=True
            )
            db.session.add(insurer)
            db.session.commit()
        
        # Step 1: Insurer logs in
        response = client.post('/auth/login', data={
            'email': 'workflowinsurer@test.com',
            'password': 'Password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 2: Navigate to dashboard
        response = client.get('/insurer/dashboard')
        assert response.status_code == 200
        
        # Step 3: Access create policy page
        response = client.get('/insurer/create-policy')
        assert response.status_code == 200
        
        # Step 4: Create policy
        response = client.post('/insurer/create-policy', data={
            'policy_number': 'WF-POL-001',
            'insured_name': 'Workflow Test',
            'email_address': 'workflow@example.com',
            'phone_number': '0712345678',
            'registration_number': 'KEE123E',
            'chassis_number': 'CH987654321',
            'make_model': 'Honda Civic',
            'vehicle_make': 'Honda',
            'vehicle_model': 'Civic',
            'year_of_manufacture': '2021',
            'policy_type': 'Comprehensive',
            'effective_date': datetime.now().strftime('%Y-%m-%d'),
            'expiry_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'premium_amount': '60000',
            'sum_insured': '2500000'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 5: Verify policy exists
        with app.app_context():
            from models import Policy
            policy = Policy.query.filter_by(policy_number='WF-POL-001').first()
            assert policy is not None
            policy_id = policy.id
        
        # Step 6: Access create claim page
        response = client.get('/insurer/create-claim')
        assert response.status_code == 200


class TestCustomerPolicyRequestWorkflow:
    """Test customer requesting policy access and insurer approval"""
    
    def test_complete_policy_request_cycle(self, client, app):
        """Test customer requests access and insurer approves"""
        
        # Setup: Create customer, insurer, and policy
        with app.app_context():
            from models import Customer, Insurer, Policy, InsuranceCompany
            from werkzeug.security import generate_password_hash
            
            # Create customer
            customer = Customer(
                username='requestcustomer',
                email='requestcustomer@test.com',
                password=generate_password_hash('Password123'),
                is_active=True
            )
            db.session.add(customer)
            
            # Create insurer
            company = InsuranceCompany.query.first()
            insurer = Insurer(
                username='approverinsurer',
                email='approverinsurer@test.com',
                password=generate_password_hash('Password123'),
                staff_id='APP001',
                insurance_company_id=company.id,
                is_approved=True,
                is_active=True
            )
            db.session.add(insurer)
            db.session.commit()
            
            # Create policy
            policy = Policy(
                policy_number='REQ-POL-001',
                insured_name='Request Customer',
                email_address='other@example.com',  # Different email initially
                registration_number='KFF123F',
                insurance_company_id=company.id,
                entered_by=insurer.id,
                effective_date=datetime.now().date(),
                expiry_date=(datetime.now() + timedelta(days=365)).date(),
                status='Active'
            )
            db.session.add(policy)
            db.session.commit()
            policy_id = policy.id
        
        # Step 1: Customer logs in
        client.post('/auth/login', data={
            'email': 'requestcustomer@test.com',
            'password': 'Password123'
        })
        
        # Step 2: Customer searches for policy
        response = client.post('/customer/search-policy', data={
            'policy_number': 'REQ-POL-001'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 3: Customer requests access
        response = client.post('/customer/request-policy-access', data={
            'policy_id': policy_id,
            'reason': 'This is my vehicle policy'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify request was created
        with app.app_context():
            from models import CustomerPolicyRequest
            request = CustomerPolicyRequest.query.filter_by(policy_id=policy_id).first()
            assert request is not None
            assert request.status == 'pending'
            request_id = request.id
        
        # Step 4: Customer logs out, insurer logs in
        client.get('/logout')
        client.post('/auth/login', data={
            'email': 'approverinsurer@test.com',
            'password': 'Password123'
        })
        
        # Step 5: Insurer views requests
        response = client.get('/insurer/customer-requests')
        assert response.status_code == 200
        
        # Step 6: Insurer approves request
        response = client.post(f'/insurer/approve-access-request/{request_id}', data={
            'notes': 'Approved - verified ownership'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify request was approved and policy email updated
        with app.app_context():
            from models import CustomerPolicyRequest, Policy
            request = CustomerPolicyRequest.query.get(request_id)
            assert request.status == 'approved'
            
            policy = Policy.query.get(policy_id)
            assert policy.email_address == 'requestcustomer@test.com'
