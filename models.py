
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
	
	# Relationships
	insurance_company = db.relationship('InsuranceCompany', backref='policies', lazy=True)
	creator = db.relationship('Insurer', backref='created_policies', lazy=True)
	photos = db.relationship('PolicyPhoto', backref='policy', lazy=True, cascade='all, delete-orphan')

class PolicyPhoto(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
	photo_type = db.Column(db.String(50), nullable=False)  # front_view, left_side, etc.
	file_path = db.Column(db.String(500), nullable=False)
	uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
