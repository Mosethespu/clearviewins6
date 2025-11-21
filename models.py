
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
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	
	def get_id(self):
		return f"regulator_{self.id}"
