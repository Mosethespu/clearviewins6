
from flask_login import UserMixin
from extension import db

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

class Insurer(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(150), unique=True, nullable=False)
	email = db.Column(db.String(150), unique=True, nullable=False)
	password = db.Column(db.String(256), nullable=False)
	staff_id = db.Column(db.String(50), unique=True, nullable=True)
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	
	def get_id(self):
		return f"insurer_{self.id}"

class Regulator(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(150), unique=True, nullable=False)
	email = db.Column(db.String(150), unique=True, nullable=False)
	password = db.Column(db.String(256), nullable=False)
	staff_id = db.Column(db.String(50), unique=True, nullable=True)
	is_active = db.Column(db.Boolean, default=True, nullable=False)
	
	def get_id(self):
		return f"regulator_{self.id}"
