
from extension import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Admin(UserMixin, db.Model):
	__tablename__ = 'admins'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(128), nullable=False)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

class Customer(UserMixin, db.Model):
	__tablename__ = 'customers'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(128), nullable=False)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

class Insurer(UserMixin, db.Model):
	__tablename__ = 'insurers'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	staff_id = db.Column(db.String(64), unique=True, nullable=False)
	password_hash = db.Column(db.String(128), nullable=False)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

class Regulator(UserMixin, db.Model):
	__tablename__ = 'regulators'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	staff_id = db.Column(db.String(64), unique=True, nullable=False)
	password_hash = db.Column(db.String(128), nullable=False)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

def create_admin_account():
	from .extension import db
	admin = Admin.query.filter_by(username='admin').first()
	if not admin:
		admin = Admin(username='admin', email='admin@clearinsure.com')
		admin.set_password('Admin@1234')
		db.session.add(admin)
		db.session.commit()
