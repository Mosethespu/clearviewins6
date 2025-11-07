from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not current_user.is_authenticated:
			flash('Please log in to access this page.', 'warning')
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function

def role_required(role):
	def decorator(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
			if not current_user.is_authenticated or getattr(current_user, 'role', None) != role:
				flash('You do not have permission to access this page.', 'danger')
				return redirect(url_for('login'))
			return f(*args, **kwargs)
		return decorated_function
	return decorator
