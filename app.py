
from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from extension import db, login_manager, migrate, cache
from models import Admin, Customer, Insurer, Regulator
from forms import SignupForm, LoginForm
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from decorators import admin_required, customer_required, insurer_required, regulator_required

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)
cache.init_app(app)

with app.app_context():
	# Ensure tables exist if migrations not yet applied (safe create)
	try:
		db.create_all()
		# Create default admin if not exists
		admin_exists = Admin.query.filter_by(email='admin@clearinsure.com').first()
		if not admin_exists:
			default_admin = Admin(
				username='admin',
				email='admin@clearinsure.com',
				password=generate_password_hash('Admin@123'),
				staff_id='ADMIN001'
			)
			db.session.add(default_admin)
			db.session.commit()
			print("\n" + "="*60)
			print("DEFAULT ADMIN CREDENTIALS CREATED")
			print("="*60)
			print("Email: admin@clearinsure.com")
			print("Password: Admin@123")
			print("Staff ID: ADMIN001")
			print("="*60 + "\n")
	except Exception as e:
		app.logger.warning(f"Database initialization warning: {e}")

@login_manager.user_loader
def load_user(user_id):
	# Parse the prefixed user ID (e.g., "admin_1", "customer_2")
	if '_' not in user_id:
		return None
	
	user_type, user_pk = user_id.split('_', 1)
	
	model_map = {
		'admin': Admin,
		'customer': Customer,
		'insurer': Insurer,
		'regulator': Regulator
	}
	
	model = model_map.get(user_type)
	if model:
		return model.query.get(int(user_pk))
	return None

@app.route('/')
def landing():
	return render_template('landing.html')

@app.route('/blog')
def blog():
	return render_template('blog.html')

@app.route('/contact')
def contact():
	return render_template('contact.html')

@app.route('/features')
def features():
	return render_template('features.html')

@app.route('/auth/signup', methods=['GET', 'POST'])
def signup():
	form = SignupForm()
	if form.validate_on_submit():
		username = form.username.data
		email = form.email.data
		password = form.password.data
		user_type = form.user_type.data
		# Only allow signup for customer, insurer, regulator (no admin self-signup)
		allowed_types = {'customer', 'insurer', 'regulator'}
		if user_type not in allowed_types:
			flash('Invalid user type.', 'danger')
			return render_template('signup.html', form=form)
		staff_id = form.staff_id.data if user_type in ['insurer', 'regulator'] else None
		hashed_password = generate_password_hash(password)
		# Check if user exists in any table
		exists = False
		for model in [Admin, Customer, Insurer, Regulator]:
			if model.query.filter((model.username==username)|(model.email==email)).first():
				exists = True
				break
		if exists:
			flash('Username or email already exists.', 'danger')
			return render_template('signup.html', form=form)
		# Create user in correct table
		if user_type == 'customer':
			user = Customer(username=username, email=email, password=hashed_password)
		elif user_type == 'insurer':
			user = Insurer(username=username, email=email, password=hashed_password, staff_id=staff_id)
		elif user_type == 'regulator':
			user = Regulator(username=username, email=email, password=hashed_password, staff_id=staff_id)
		else:
			flash('Invalid user type.', 'danger')
			return render_template('signup.html', form=form)
		db.session.add(user)
		db.session.commit()
		flash('Sign up successful! Please log in.', 'success')
		return redirect(url_for('login'))
	return render_template('signup.html', form=form)

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		email = form.email.data.strip()
		password = form.password.data
		# Try each user table
		for model, endpoint in [
			(Admin, 'admin_dashboard'),
			(Customer, 'customer_dashboard'),
			(Insurer, 'insurer_dashboard'),
			(Regulator, 'regulator_dashboard')
		]:
			user = model.query.filter_by(email=email).first()
			if user and check_password_hash(user.password, password):
				# Check if user is active
				if not user.is_active:
					flash('Your account has been disabled. Please contact the administrator.', 'danger')
					return render_template('login.html', form=form)
				login_user(user)
				flash('Login successful!', 'success')
				return redirect(url_for(endpoint))
		else:
			flash('Invalid credentials.', 'danger')
	return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
	# Redirect to appropriate dashboard based on user type
	user_class = current_user.__class__.__name__
	if user_class == 'Admin':
		return redirect(url_for('admin_dashboard'))
	elif user_class == 'Customer':
		return redirect(url_for('customer_dashboard'))
	elif user_class == 'Insurer':
		return redirect(url_for('insurer_dashboard'))
	elif user_class == 'Regulator':
		return redirect(url_for('regulator_dashboard'))
	else:
		flash('Unknown user type.', 'danger')
		return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('Logged out successfully.', 'info')
	return redirect(url_for('login'))

@app.route('/forgotpassword')
def forgot_password():
	return render_template('forgotpassword.html')

# Dashboard routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
	customers = Customer.query.all()
	insurers = Insurer.query.all()
	regulators = Regulator.query.all()
	return render_template('admin/admindashboard.html', customers=customers, insurers=insurers, regulators=regulators)

@app.route('/admin/user-management')
@login_required
@admin_required
def user_management():
	customers = Customer.query.all()
	insurers = Insurer.query.all()
	regulators = Regulator.query.all()
	return render_template('admin/usermanagement.html', customers=customers, insurers=insurers, regulators=regulators)

@app.route('/admin/toggle-user/<user_type>/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_type, user_id):
	model_map = {
		'customer': Customer,
		'insurer': Insurer,
		'regulator': Regulator
	}
	model = model_map.get(user_type)
	if not model:
		flash('Invalid user type.', 'danger')
		return redirect(url_for('user_management'))
	
	user = model.query.get_or_404(user_id)
	user.is_active = not user.is_active
	db.session.commit()
	
	status = 'enabled' if user.is_active else 'disabled'
	flash(f'User {user.username} has been {status}.', 'success')
	return redirect(url_for('user_management'))

@app.route('/admin/edit-user/<user_type>/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_type, user_id):
	model_map = {
		'customer': Customer,
		'insurer': Insurer,
		'regulator': Regulator
	}
	model = model_map.get(user_type)
	if not model:
		flash('Invalid user type.', 'danger')
		return redirect(url_for('user_management'))
	
	user = model.query.get_or_404(user_id)
	
	if request.method == 'POST':
		username = request.form.get('username')
		email = request.form.get('email')
		
		# Check if username/email already exists for another user
		for m in [Customer, Insurer, Regulator]:
			existing = m.query.filter(
				((m.username == username) | (m.email == email)) & (m.id != user_id)
			).first()
			if existing:
				flash('Username or email already exists.', 'danger')
				return render_template('admin/edituser.html', user=user, user_type=user_type)
		
		user.username = username
		user.email = email
		
		# Update staff_id if applicable
		if user_type in ['insurer', 'regulator']:
			staff_id = request.form.get('staff_id')
			user.staff_id = staff_id
		
		# Update password if provided
		new_password = request.form.get('password')
		if new_password:
			user.password = generate_password_hash(new_password)
		
		db.session.commit()
		flash(f'User {user.username} updated successfully.', 'success')
		return redirect(url_for('user_management'))
	
	return render_template('admin/edituser.html', user=user, user_type=user_type)

@app.route('/customer/dashboard')
@login_required
@customer_required
def customer_dashboard():
	return render_template('customer/customerashboard.html')

@app.route('/insurer/dashboard')
@login_required
@insurer_required
def insurer_dashboard():
	return render_template('insurer/insurerdashboard.html')

@app.route('/regulator/dashboard')
@login_required
@regulator_required
def regulator_dashboard():
	return render_template('regulator/regulatordashboard.html')

if __name__ == '__main__':
	app.run(debug=True)