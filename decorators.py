
from flask import redirect, url_for, flash
from flask_login import current_user
from functools import wraps

def admin_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not hasattr(current_user, 'username') or not current_user.is_authenticated or current_user.__class__.__name__ != 'Admin':
			flash('Admin access required.', 'danger')
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function

def customer_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not hasattr(current_user, 'username') or not current_user.is_authenticated or current_user.__class__.__name__ != 'Customer':
			flash('Customer access required.', 'danger')
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function

def insurer_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not hasattr(current_user, 'username') or not current_user.is_authenticated or current_user.__class__.__name__ != 'Insurer':
			flash('Insurer access required.', 'danger')
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function

def regulator_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not hasattr(current_user, 'username') or not current_user.is_authenticated or current_user.__class__.__name__ != 'Regulator':
			flash('Regulator access required.', 'danger')
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function
