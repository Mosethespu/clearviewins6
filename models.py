
from flask_login import UserMixin
from extension import db
from datetime import datetime

class Admin(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(150), unique=True, nullable=False)
	email = db.Column(db.String(150), unique=True, nullable=False)
	password = db.Column(db.String(256), nullable=False)
	staff_id = db.Column(db.String(50), unique=True, nullable=True)
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	
	def get_id(self):
		return f"admin_{self.id}"

class Customer(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(150), unique=True, nullable=False)
	email = db.Column(db.String(150), unique=True, nullable=False)
	password = db.Column(db.String(256), nullable=False)
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	
	def get_id(self):
		return f"customer_{self.id}"

class InsuranceCompany(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(200), unique=True, nullable=False)
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	insurers = db.relationship('Insurer', backref='company', lazy=True)

class RegulatoryBody(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(200), unique=True, nullable=False)
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	regulators = db.relationship('Regulator', backref='regulatory_body', lazy=True)

class Insurer(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(150), unique=True, nullable=False)
	email = db.Column(db.String(150), unique=True, nullable=False)
	password = db.Column(db.String(256), nullable=False)
	staff_id = db.Column(db.String(50), unique=True, nullable=True)
	insurance_company_id = db.Column(db.Integer, db.ForeignKey('insurance_company.id'), nullable=True)
	is_approved = db.Column(db.Boolean, default=False, nullable=False)
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	approval_date = db.Column(db.DateTime, nullable=True)
	
	def get_id(self):
		return f"insurer_{self.id}"

class InsurerRequest(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	insurer_id = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=False)
	staff_id = db.Column(db.String(50), nullable=False)
	insurance_company_id = db.Column(db.Integer, db.ForeignKey('insurance_company.id'), nullable=False)
	status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
	request_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	reviewed_date = db.Column(db.DateTime, nullable=True)
	reviewed_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
	rejection_reason = db.Column(db.Text, nullable=True)
	
	insurer = db.relationship('Insurer', backref='requests', lazy=True)
	insurance_company = db.relationship('InsuranceCompany', backref='requests', lazy=True)
	reviewer = db.relationship('Admin', backref='reviewed_requests', lazy=True)

class Regulator(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(150), unique=True, nullable=False)
	email = db.Column(db.String(150), unique=True, nullable=False)
	password = db.Column(db.String(256), nullable=False)
	staff_id = db.Column(db.String(50), unique=True, nullable=True)
	regulatory_body_id = db.Column(db.Integer, db.ForeignKey('regulatory_body.id'), nullable=True)
	is_approved = db.Column(db.Boolean, default=False, nullable=False)
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	approval_date = db.Column(db.DateTime, nullable=True)
	
	def get_id(self):
		return f"regulator_{self.id}"

class RegulatorRequest(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	regulator_id = db.Column(db.Integer, db.ForeignKey('regulator.id'), nullable=False)
	staff_id = db.Column(db.String(50), nullable=False)
	regulatory_body_id = db.Column(db.Integer, db.ForeignKey('regulatory_body.id'), nullable=False)
	status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
	request_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	reviewed_date = db.Column(db.DateTime, nullable=True)
	reviewed_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
	rejection_reason = db.Column(db.Text, nullable=True)
	
	regulator = db.relationship('Regulator', backref='requests', lazy=True)
	regulatory_body = db.relationship('RegulatoryBody', backref='requests', lazy=True)
	reviewer = db.relationship('Admin', backref='reviewed_regulator_requests', lazy=True)

class Policy(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	policy_number = db.Column(db.String(50), unique=True, nullable=False)
	policy_type = db.Column(db.String(50), nullable=False)  # Comprehensive, Third-Party Only, Third-Party Fire & Theft
	effective_date = db.Column(db.Date, nullable=False)
	expiry_date = db.Column(db.Date, nullable=False)
	premium_amount = db.Column(db.Float, nullable=False)
	payment_mode = db.Column(db.String(50), nullable=False)
	
	# Insured Details
	insured_name = db.Column(db.String(200), nullable=False)
	national_id = db.Column(db.String(50), nullable=False)
	kra_pin = db.Column(db.String(50), nullable=True)
	date_of_birth = db.Column(db.Date, nullable=False)
	phone_number = db.Column(db.String(20), nullable=False)
	email_address = db.Column(db.String(150), nullable=False)
	postal_address = db.Column(db.Text, nullable=True)
	
	# Vehicle Details
	registration_number = db.Column(db.String(50), nullable=False)
	make_model = db.Column(db.String(150), nullable=False)
	year_of_manufacture = db.Column(db.Integer, nullable=False)
	chassis_number = db.Column(db.String(100), nullable=False)
	engine_number = db.Column(db.String(100), nullable=False)
	body_type = db.Column(db.String(50), nullable=False)
	color = db.Column(db.String(50), nullable=False)
	seating_capacity = db.Column(db.Integer, nullable=False)
	use_category = db.Column(db.String(50), nullable=False)
	
	# Coverage Details
	sum_insured = db.Column(db.Float, nullable=False)
	excess = db.Column(db.Float, nullable=False)
	political_violence = db.Column(db.Boolean, default=False)
	windscreen_cover = db.Column(db.Boolean, default=False)
	passenger_liability = db.Column(db.Boolean, default=False)
	road_rescue = db.Column(db.Boolean, default=False)
	
	# Agent/Company Detailsi
	insurance_company_id = db.Column(db.Integer, db.ForeignKey('insurance_company.id'), nullable=False)
	created_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=False)
	date_entered = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	status = db.Column(db.String(20), default='Active', nullable=False)  # Active, Expired, Cancelled
	cancelled_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=True)
	cancellation_date = db.Column(db.DateTime, nullable=True)
	cancellation_reason = db.Column(db.Text, nullable=True)
	
	# Relationships
	insurance_company = db.relationship('InsuranceCompany', backref='policies', lazy=True)
	creator = db.relationship('Insurer', backref='created_policies', lazy=True, foreign_keys=[created_by])
	canceller = db.relationship('Insurer', backref='cancelled_policies', lazy=True, foreign_keys=[cancelled_by])
	photos = db.relationship('PolicyPhoto', backref='policy', lazy=True, cascade='all, delete-orphan')

class PolicyPhoto(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
	photo_type = db.Column(db.String(50), nullable=False)  # front_view, left_side, etc.
	file_path = db.Column(db.String(500), nullable=False)
	uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Claim(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	claim_number = db.Column(db.String(20), unique=True, nullable=False)
	
	# Section A: Policy Information (auto-filled from policy)
	policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
	insurance_company_id = db.Column(db.Integer, db.ForeignKey('insurance_company.id'), nullable=False)
	
	# Section C: Accident Details
	accident_date = db.Column(db.Date, nullable=False)
	accident_time = db.Column(db.Time, nullable=False)
	accident_location = db.Column(db.String(500), nullable=False)
	accident_description = db.Column(db.Text, nullable=False)
	weather_conditions = db.Column(db.String(50), nullable=False)  # Clear, Rainy, Foggy, etc.
	police_report_number = db.Column(db.String(100), nullable=False)
	vehicle_towed = db.Column(db.Boolean, default=False, nullable=False)
	tow_location = db.Column(db.String(300))
	
	# Section D: Damage & Injuries
	damage_insured_vehicle = db.Column(db.Text, nullable=False)
	damage_third_party = db.Column(db.Text)
	injuries_driver_passengers = db.Column(db.Text)
	injuries_third_parties = db.Column(db.Text)
	
	# Section F: Witness Information
	witness_name = db.Column(db.String(200))
	witness_contact = db.Column(db.String(20))
	witness_statement = db.Column(db.Text)
	
	# System fields
	status = db.Column(db.String(50), default='Pending', nullable=False)  # Pending, Under Review, Approved, Rejected
	created_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=False)
	date_submitted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	
	# Review fields
	reviewed_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=True)
	review_date = db.Column(db.DateTime, nullable=True)
	review_notes = db.Column(db.Text, nullable=True)
	
	# Fraud check fields
	fraud_check_performed = db.Column(db.Boolean, default=False, nullable=False)
	fraud_check_date = db.Column(db.DateTime, nullable=True)
	fraud_check_result = db.Column(db.Text, nullable=True)
	fraud_risk_score = db.Column(db.Float, nullable=True)  # 0-100 score
	
	# Approval/Rejection fields
	approved_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=True)
	approval_date = db.Column(db.DateTime, nullable=True)
	rejection_reason = db.Column(db.Text, nullable=True)
	
	# Relationships
	policy = db.relationship('Policy', backref='claims')
	insurance_company = db.relationship('InsuranceCompany', backref='claims')
	documents = db.relationship('ClaimDocument', backref='claim', cascade='all, delete-orphan')
	creator = db.relationship('Insurer', backref='claims_created', foreign_keys=[created_by])
	reviewer = db.relationship('Insurer', backref='claims_reviewed', foreign_keys=[reviewed_by])
	approver = db.relationship('Insurer', backref='claims_approved', foreign_keys=[approved_by])


class ClaimDocument(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	claim_id = db.Column(db.Integer, db.ForeignKey('claim.id'), nullable=False)
	document_type = db.Column(db.String(100), nullable=False)  # accident_photo, police_abstract, driver_license, logbook, etc.
	file_path = db.Column(db.String(500), nullable=False)
	uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class PremiumRate(db.Model):
	"""Insurance company-specific premium rates"""
	id = db.Column(db.Integer, primary_key=True)
	insurance_company_id = db.Column(db.Integer, db.ForeignKey('insurance_company.id'), nullable=False)
	
	# Cover type
	cover_type = db.Column(db.String(50), nullable=False)  # Comprehensive, Third-Party Only, Third-Party Fire & Theft, PSV
	
	# Comprehensive rates (percentage of vehicle value)
	comprehensive_min_rate = db.Column(db.Float, nullable=True)  # e.g., 4.0 for 4%
	comprehensive_max_rate = db.Column(db.Float, nullable=True)  # e.g., 7.0 for 7%
	comprehensive_default_rate = db.Column(db.Float, nullable=True)  # e.g., 5.0 for 5%
	
	# Third-Party Only (flat rate)
	tpo_flat_rate = db.Column(db.Float, nullable=True)  # e.g., 8000.0
	
	# Third-Party Fire & Theft
	tpft_base_rate = db.Column(db.Float, nullable=True)  # Base TPO rate
	tpft_percentage = db.Column(db.Float, nullable=True)  # e.g., 1.5 for 1.5% of vehicle value
	
	# PSV rates (flat rates by vehicle type)
	psv_taxi_rate = db.Column(db.Float, nullable=True)  # e.g., 25000.0
	psv_matatu_14_rate = db.Column(db.Float, nullable=True)  # e.g., 70000.0
	psv_matatu_25_rate = db.Column(db.Float, nullable=True)  # e.g., 90000.0
	psv_bus_rate = db.Column(db.Float, nullable=True)  # e.g., 135000.0
	
	# Metadata
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	
	# Relationships
	insurance_company = db.relationship('InsuranceCompany', backref='premium_rates')
	
	# Unique constraint: one rate config per cover type per company
	__table_args__ = (db.UniqueConstraint('insurance_company_id', 'cover_type', name='_company_cover_uc'),)


class Quote(db.Model):
	"""Insurance quotes generated from premium calculator"""
	id = db.Column(db.Integer, primary_key=True)
	quote_number = db.Column(db.String(20), unique=True, nullable=False)
	insurance_company_id = db.Column(db.Integer, db.ForeignKey('insurance_company.id'), nullable=False)
	created_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=False)
	
	# Customer information
	customer_email = db.Column(db.String(150), nullable=False)
	customer_name = db.Column(db.String(200), nullable=True)
	customer_phone = db.Column(db.String(20), nullable=True)
	
	# Vehicle information
	vehicle_value = db.Column(db.Float, nullable=False)
	registration_number = db.Column(db.String(50), nullable=True)
	make_model = db.Column(db.String(150), nullable=True)
	year_of_manufacture = db.Column(db.Integer, nullable=True)
	
	# Coverage details
	cover_type = db.Column(db.String(50), nullable=False)  # Comprehensive, Third-Party Only, etc.
	use_category = db.Column(db.String(50), nullable=True)  # Private, Commercial, PSV
	
	# Premium calculation
	base_premium = db.Column(db.Float, nullable=False)
	rate_applied = db.Column(db.Float, nullable=True)  # Percentage or flat rate used
	final_premium = db.Column(db.Float, nullable=False)
	
	# Add-ons (optional extras)
	political_violence = db.Column(db.Boolean, default=False)
	windscreen_cover = db.Column(db.Boolean, default=False)
	passenger_liability = db.Column(db.Boolean, default=False)
	road_rescue = db.Column(db.Boolean, default=False)
	
	# Status
	status = db.Column(db.String(20), default='Sent', nullable=False)  # Sent, Accepted, Converted, Expired
	
	# Timestamps
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	valid_until = db.Column(db.DateTime, nullable=True)  # Quote expiry date
	
	# Relationships
	insurance_company = db.relationship('InsuranceCompany', backref='quotes')
	creator = db.relationship('Insurer', backref='quotes_created')


class CustomerMonitoredPolicy(db.Model):
	"""Policies that customers are monitoring (view-only access)"""
	id = db.Column(db.Integer, primary_key=True)
	customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
	policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
	date_added = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	
	# Relationships
	customer = db.relationship('Customer', backref='monitored_policies')
	policy = db.relationship('Policy', backref='monitoring_customers')
	
	# Unique constraint: one customer can't monitor the same policy twice
	__table_args__ = (db.UniqueConstraint('customer_id', 'policy_id', name='_customer_policy_monitor_uc'),)


class CustomerPolicyRequest(db.Model):
	"""Customer requests to add a policy to their account (full access)"""
	id = db.Column(db.Integer, primary_key=True)
	customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
	policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
	request_type = db.Column(db.String(20), default='access', nullable=False)  # access
	status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
	request_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	request_reason = db.Column(db.Text, nullable=True)
	
	# Review details
	reviewed_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=True)
	reviewed_date = db.Column(db.DateTime, nullable=True)
	review_notes = db.Column(db.Text, nullable=True)
	rejection_reason = db.Column(db.Text, nullable=True)
	
	# Relationships
	customer = db.relationship('Customer', backref='policy_requests')
	policy = db.relationship('Policy', backref='access_requests')
	reviewer = db.relationship('Insurer', backref='reviewed_policy_requests')


class PolicyCancellationRequest(db.Model):
	"""Customer requests to cancel their policy"""
	id = db.Column(db.Integer, primary_key=True)
	customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
	policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
	request_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	cancellation_reason = db.Column(db.Text, nullable=False)
	status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
	
	# Review details
	reviewed_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=True)
	reviewed_date = db.Column(db.DateTime, nullable=True)
	review_notes = db.Column(db.Text, nullable=True)
	rejection_reason = db.Column(db.Text, nullable=True)
	
	# Relationships
	customer = db.relationship('Customer', backref='cancellation_requests')
	policy = db.relationship('Policy', backref='cancellation_requests')
	reviewer = db.relationship('Insurer', backref='reviewed_cancellation_requests')


class PolicyRenewalRequest(db.Model):
	"""Customer requests to renew their policy"""
	id = db.Column(db.Integer, primary_key=True)
	customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
	policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
	request_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	
	# New renewal dates (auto-calculated)
	new_effective_date = db.Column(db.Date, nullable=False)
	new_expiry_date = db.Column(db.Date, nullable=False)
	renewal_premium = db.Column(db.Float, nullable=True)  # Can be adjusted by insurer
	
	status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
	
	# Review details
	reviewed_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=True)
	reviewed_date = db.Column(db.DateTime, nullable=True)
	review_notes = db.Column(db.Text, nullable=True)
	rejection_reason = db.Column(db.Text, nullable=True)
	
	# Relationships
	customer = db.relationship('Customer', backref='renewal_requests')
	policy = db.relationship('Policy', backref='renewal_requests')
	reviewer = db.relationship('Insurer', backref='reviewed_renewal_requests')


class BlogPost(db.Model):
	"""Blog posts created by admins"""
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	slug = db.Column(db.String(250), unique=True, nullable=False)  # URL-friendly title
	excerpt = db.Column(db.Text, nullable=False)  # Short summary for cards
	content = db.Column(db.Text, nullable=False)  # Full blog content
	author_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
	published = db.Column(db.Boolean, default=False, nullable=False)
	featured_image = db.Column(db.String(255), nullable=True)  # Path to image
	views = db.Column(db.Integer, default=0, nullable=False)
	
	# Relationships
	author = db.relationship('Admin', backref='blog_posts')


class ContactMessage(db.Model):
	"""Contact form submissions"""
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(150), nullable=False)
	email = db.Column(db.String(150), nullable=False)
	message = db.Column(db.Text, nullable=False)
	submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	read = db.Column(db.Boolean, default=False, nullable=False)
	read_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
	read_at = db.Column(db.DateTime, nullable=True)
	
	# Relationship
	reader = db.relationship('Admin', backref='read_contact_messages')

