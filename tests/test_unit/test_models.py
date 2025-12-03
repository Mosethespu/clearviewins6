"""
Unit tests for database models
Tests model creation, relationships, and validations
"""
import pytest
from models import Admin, Customer, Insurer, Regulator, Policy, Claim, BlogPost, ContactMessage
from extension import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta


class TestUserModels:
    """Test user model functionality"""
    
    def test_admin_creation(self, app):
        """Test creating an admin user"""
        with app.app_context():
            admin = Admin(
                username='admin1',
                email='admin1@test.com',
                password=generate_password_hash('password'),
                staff_id='A001'
            )
            db.session.add(admin)
            db.session.commit()
            
            assert admin.id is not None
            assert admin.username == 'admin1'
            assert admin.get_id() == f'admin_{admin.id}'
            assert check_password_hash(admin.password, 'password')
    
    def test_customer_creation(self, app):
        """Test creating a customer user"""
        with app.app_context():
            customer = Customer(
                username='customer1',
                email='customer1@test.com',
                password=generate_password_hash('password')
            )
            db.session.add(customer)
            db.session.commit()
            
            assert customer.id is not None
            assert customer.get_id() == f'customer_{customer.id}'
            assert customer.is_active is True
    
    def test_insurer_creation(self, app):
        """Test creating an insurer user"""
        with app.app_context():
            from models import InsuranceCompany
            company = InsuranceCompany.query.first()
            
            insurer = Insurer(
                username='insurer1',
                email='insurer1@test.com',
                password=generate_password_hash('password'),
                staff_id='I001',
                insurance_company_id=company.id,
                is_approved=False
            )
            db.session.add(insurer)
            db.session.commit()
            
            assert insurer.id is not None
            assert insurer.get_id() == f'insurer_{insurer.id}'
            assert insurer.is_approved is False
            assert insurer.company == company
    
    def test_regulator_creation(self, app):
        """Test creating a regulator user"""
        with app.app_context():
            from models import RegulatoryBody
            reg_body = RegulatoryBody.query.first()
            
            regulator = Regulator(
                username='regulator1',
                email='regulator1@test.com',
                password=generate_password_hash('password'),
                staff_id='R001',
                regulatory_body_id=reg_body.id,
                is_approved=True
            )
            db.session.add(regulator)
            db.session.commit()
            
            assert regulator.id is not None
            assert regulator.get_id() == f'regulator_{regulator.id}'
            assert regulator.regulatory_body == reg_body


class TestPolicyModel:
    """Test policy model functionality"""
    
    def test_policy_creation(self, app, insurer_user):
        """Test creating a policy"""
        with app.app_context():
            insurer = Insurer.query.filter_by(email='insurer@test.com').first()
            
            policy = Policy(
                policy_number='POL-TEST-001',
                insured_name='John Doe',
                email_address='john@test.com',
                registration_number='KAA123B',
                chassis_number='CH123456789',
                make_model='Toyota Camry',
                vehicle_make='Toyota',
                vehicle_model='Camry',
                year_of_manufacture=2020,
                policy_type='Comprehensive',
                effective_date=datetime.now().date(),
                expiry_date=datetime.now().date() + timedelta(days=365),
                premium_amount=50000.0,
                sum_insured=2000000.0,
                insurance_company_id=insurer.insurance_company_id,
                entered_by=insurer.id,
                status='Active'
            )
            db.session.add(policy)
            db.session.commit()
            
            assert policy.id is not None
            assert policy.policy_number == 'POL-TEST-001'
            assert policy.status == 'Active'
    
    def test_policy_relationships(self, app, insurer_user):
        """Test policy relationships with photos and claims"""
        with app.app_context():
            from models import PolicyPhoto
            insurer = Insurer.query.filter_by(email='insurer@test.com').first()
            
            policy = Policy(
                policy_number='POL-TEST-002',
                insured_name='Jane Doe',
                email_address='jane@test.com',
                registration_number='KBB456C',
                insurance_company_id=insurer.insurance_company_id,
                entered_by=insurer.id
            )
            db.session.add(policy)
            db.session.commit()
            
            # Add photo
            photo = PolicyPhoto(
                policy_id=policy.id,
                file_path='test/photo.jpg',
                uploaded_at=datetime.utcnow()
            )
            db.session.add(photo)
            db.session.commit()
            
            assert len(policy.photos) == 1
            assert policy.photos[0].file_path == 'test/photo.jpg'


class TestClaimModel:
    """Test claim model functionality"""
    
    def test_claim_creation(self, app, insurer_user):
        """Test creating a claim"""
        with app.app_context():
            insurer = Insurer.query.filter_by(email='insurer@test.com').first()
            
            # Create policy first
            policy = Policy(
                policy_number='POL-CLAIM-001',
                insured_name='Test User',
                email_address='test@test.com',
                registration_number='KCC789D',
                insurance_company_id=insurer.insurance_company_id,
                entered_by=insurer.id
            )
            db.session.add(policy)
            db.session.commit()
            
            # Create claim
            claim = Claim(
                claim_number='CLM-TEST-001',
                policy_id=policy.id,
                insurance_company_id=insurer.insurance_company_id,
                accident_date=datetime.now().date(),
                accident_location='Nairobi',
                accident_description='Rear-end collision',
                police_report_number='PR123456',
                estimated_loss=100000.0,
                status='Pending',
                filed_by=insurer.id
            )
            db.session.add(claim)
            db.session.commit()
            
            assert claim.id is not None
            assert claim.claim_number == 'CLM-TEST-001'
            assert claim.policy == policy


class TestBlogPostModel:
    """Test blog post model functionality"""
    
    def test_blog_post_creation(self, app, admin_user):
        """Test creating a blog post"""
        with app.app_context():
            admin = Admin.query.filter_by(email='admin@test.com').first()
            
            post = BlogPost(
                title='Test Blog Post',
                slug='test-blog-post',
                excerpt='This is a test excerpt',
                content='<p>This is the full content</p>',
                author_id=admin.id,
                published=True
            )
            db.session.add(post)
            db.session.commit()
            
            assert post.id is not None
            assert post.slug == 'test-blog-post'
            assert post.author == admin
            assert post.views == 0


class TestContactMessageModel:
    """Test contact message model functionality"""
    
    def test_contact_message_creation(self, app):
        """Test creating a contact message"""
        with app.app_context():
            message = ContactMessage(
                name='Test User',
                email='test@example.com',
                message='This is a test message'
            )
            db.session.add(message)
            db.session.commit()
            
            assert message.id is not None
            assert message.read is False
            assert message.submitted_at is not None
