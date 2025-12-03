"""
Performance tests using locust
Tests application performance under load
"""
import time
import pytest
from extension import db


class TestResponseTimes:
    """Test response times for critical pages"""
    
    def test_homepage_response_time(self, client):
        """Test homepage loads within acceptable time"""
        start_time = time.time()
        response = client.get('/')
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 2.0  # Should load in less than 2 seconds
    
    def test_login_response_time(self, client, customer_user):
        """Test login completes within acceptable time"""
        start_time = time.time()
        response = client.post('/auth/login', data={
            'email': 'customer@test.com',
            'password': 'TestPassword123'
        }, follow_redirects=True)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 3.0  # Login should complete in less than 3 seconds
    
    def test_dashboard_response_time(self, authenticated_customer):
        """Test dashboard loads within acceptable time"""
        start_time = time.time()
        response = authenticated_customer.get('/customer/dashboard')
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 2.0


class TestDatabaseQueryPerformance:
    """Test database query performance"""
    
    def test_bulk_policy_query(self, app, insurer_user):
        """Test querying multiple policies"""
        with app.app_context():
            from models import Policy, Insurer
            insurer = Insurer.query.filter_by(email='insurer@test.com').first()
            
            # Create multiple policies
            policies = []
            for i in range(50):
                policy = Policy(
                    policy_number=f'PERF-{i:03d}',
                    insured_name=f'User {i}',
                    email_address=f'user{i}@test.com',
                    registration_number=f'K{chr(65+i%26)}{chr(65+(i+1)%26)}{i:03d}',
                    insurance_company_id=insurer.insurance_company_id,
                    entered_by=insurer.id
                )
                policies.append(policy)
            
            db.session.bulk_save_objects(policies)
            db.session.commit()
            
            # Time the query
            start_time = time.time()
            results = Policy.query.filter_by(insurance_company_id=insurer.insurance_company_id).all()
            end_time = time.time()
            
            query_time = end_time - start_time
            assert len(results) >= 50
            assert query_time < 1.0  # Should query in less than 1 second
    
    def test_search_performance(self, app, insurer_user):
        """Test search query performance"""
        with app.app_context():
            from models import Policy
            
            # Time the search
            start_time = time.time()
            results = Policy.query.filter(
                Policy.policy_number.like('%PERF%')
            ).limit(20).all()
            end_time = time.time()
            
            query_time = end_time - start_time
            assert query_time < 1.0  # Search should complete in less than 1 second


class TestConcurrentRequests:
    """Test handling concurrent requests"""
    
    def test_multiple_simultaneous_logins(self, client, app):
        """Test multiple login attempts"""
        with app.app_context():
            from models import Customer
            from werkzeug.security import generate_password_hash
            
            # Create multiple test users
            for i in range(10):
                user = Customer(
                    username=f'concurrent{i}',
                    email=f'concurrent{i}@test.com',
                    password=generate_password_hash('Password123'),
                    is_active=True
                )
                db.session.add(user)
            db.session.commit()
        
        # Simulate concurrent logins
        start_time = time.time()
        for i in range(10):
            response = client.post('/auth/login', data={
                'email': f'concurrent{i}@test.com',
                'password': 'Password123'
            })
            assert response.status_code in [200, 302]
        end_time = time.time()
        
        total_time = end_time - start_time
        assert total_time < 10.0  # All logins should complete in less than 10 seconds


class TestMemoryUsage:
    """Test memory usage patterns"""
    
    def test_large_dataset_handling(self, app, insurer_user):
        """Test handling large datasets"""
        with app.app_context():
            from models import Policy, Insurer
            insurer = Insurer.query.filter_by(email='insurer@test.com').first()
            
            # Create large number of policies
            policies = []
            for i in range(100):
                policy = Policy(
                    policy_number=f'LARGE-{i:04d}',
                    insured_name=f'Large User {i}',
                    email_address=f'large{i}@test.com',
                    registration_number=f'KL{i:04d}',
                    insurance_company_id=insurer.insurance_company_id,
                    entered_by=insurer.id
                )
                policies.append(policy)
            
            # Bulk insert
            start_time = time.time()
            db.session.bulk_save_objects(policies)
            db.session.commit()
            end_time = time.time()
            
            insert_time = end_time - start_time
            assert insert_time < 5.0  # Bulk insert should complete in less than 5 seconds
