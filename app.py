
from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from extension import db, migrate, login_manager
from models import Admin, Customer, Insurer, Regulator, create_admin_account
# Ensure models are imported for Flask-Migrate
_models_for_migrate = [Admin, Customer, Insurer, Regulator]
from forms import CustomerSignupForm, InsurerSignupForm, RegulatorSignupForm, LoginForm
from flask_login import login_user, logout_user, current_user
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	# Try to find user in all tables
	for model in [Admin, Customer, Insurer, Regulator]:
		user = model.query.get(int(user_id))
		if user:
			# Set a role property for navbar/dashboard link
			if isinstance(user, Admin):
				user.role = 'admin'
			elif isinstance(user, Customer):
				user.role = 'customer'
			elif isinstance(user, Insurer):
				user.role = 'insurer'
			elif isinstance(user, Regulator):
				user.role = 'regulator'
			return user
	return None


# To create the initial admin account, run this function manually after migrations:
def setup_admin():
	with app.app_context():
		create_admin_account()

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

# Signup routes
@app.route('/auth/signup', methods=['GET', 'POST'])
def signup():
	user_type = request.args.get('user_type', 'customer')
	if user_type == 'customer':
		form = CustomerSignupForm()
		if form.validate_on_submit():
			if Customer.query.filter_by(username=form.username.data).first():
				flash('Username already exists.', 'danger')
			else:
				user = Customer(username=form.username.data, email=form.email.data)
				user.set_password(form.password.data)
				db.session.add(user)
				db.session.commit()
				flash('Signup successful! Please log in.', 'success')
				return redirect(url_for('login'))
		return render_template('signup.html', form=form, user_type='customer')
	elif user_type == 'insurer':
		form = InsurerSignupForm()
		if form.validate_on_submit():
			if Insurer.query.filter_by(username=form.username.data).first():
				flash('Username already exists.', 'danger')
			else:
				user = Insurer(username=form.username.data, email=form.email.data, staff_id=form.staff_id.data)
				user.set_password(form.password.data)
				db.session.add(user)
				db.session.commit()
				flash('Signup successful! Please log in.', 'success')
				return redirect(url_for('login'))
		return render_template('signup.html', form=form, user_type='insurer')
	elif user_type == 'regulator':
		form = RegulatorSignupForm()
		if form.validate_on_submit():
			if Regulator.query.filter_by(username=form.username.data).first():
				flash('Username already exists.', 'danger')
			else:
				user = Regulator(username=form.username.data, email=form.email.data, staff_id=form.staff_id.data)
				user.set_password(form.password.data)
				db.session.add(user)
				db.session.commit()
				flash('Signup successful! Please log in.', 'success')
				return redirect(url_for('login'))
		return render_template('signup.html', form=form, user_type='regulator')
	else:
		flash('Invalid user type.', 'danger')
		return redirect(url_for('signup') )

# Login route
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		username = form.username.data
		password = form.password.data
		user = None
		# Try to find user in all tables
		for model in [Admin, Customer, Insurer, Regulator]:
			candidate = model.query.filter_by(username=username).first()
			if candidate:
				user = candidate
				break
		if not user:
			flash('Username not found', 'danger')
			return render_template('login.html', form=form)
		if not user.check_password(password):
			flash('Incorrect password', 'danger')
			return render_template('login.html', form=form)
		logout_user()  # Ensure previous session is cleared
		login_user(user)
		flash('Logged in successfully!', 'success')
		if isinstance(user, Admin):
			return redirect(url_for('admin_dashboard'))
		elif isinstance(user, Customer):
			return redirect(url_for('customer_dashboard'))
		elif isinstance(user, Insurer):
			return redirect(url_for('insurer_dashboard'))
		elif isinstance(user, Regulator):
			return redirect(url_for('regulator_dashboard'))
	return render_template('login.html', form=form)
@app.route('/logout')
def logout():
	logout_user()
	flash('Logged out successfully.', 'info')
	return redirect(url_for('login'))

# Dashboards
@app.route('/admin/dashboard')
def admin_dashboard():
	if not current_user.is_authenticated or not isinstance(current_user, Admin):
		return redirect(url_for('login'))
	return render_template('admin/admindashboard.html')

@app.route('/customer/dashboard')
def customer_dashboard():
	if not current_user.is_authenticated or not isinstance(current_user, Customer):
		return redirect(url_for('login'))
	return render_template('customer/customerashboard.html')

@app.route('/insurer/dashboard')
def insurer_dashboard():
	if not current_user.is_authenticated or not isinstance(current_user, Insurer):
		return redirect(url_for('login'))
	return render_template('insurer/insurerdashboard.html')

@app.route('/regulator/dashboard')
def regulator_dashboard():
	if not current_user.is_authenticated or not isinstance(current_user, Regulator):
		return redirect(url_for('login'))
	return render_template('regulator/regulatordashboard.html')

@app.route('/forgotpassword')
def forgot_password():
	return render_template('forgotpassword.html')

if __name__ == '__main__':
	with app.app_context():
		from flask_migrate import upgrade
		upgrade()
		# Create admin account if not exists
		from models import Admin
		if not Admin.query.filter_by(username='admin').first():
			admin = Admin(username='admin', email='admin@clearinsure.com')
			admin.set_password('Admin@1234')
			db.session.add(admin)
			db.session.commit()
	app.run(debug=True)