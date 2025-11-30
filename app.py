
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from config import Config
from extension import db, login_manager, migrate, cache
from models import Admin, Customer, Insurer, Regulator, InsuranceCompany, InsurerRequest, RegulatoryBody, RegulatorRequest, Policy, PolicyPhoto
from forms import SignupForm, LoginForm, InsurerAccessRequestForm, RegulatorAccessRequestForm, PolicyCreationForm
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from decorators import admin_required, customer_required, insurer_required, regulator_required
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)
cache.init_app(app)

# Insurance companies data
INSURANCE_COMPANIES = [
	"AAR Insurance Kenya Ltd",
	"Africa Merchant Assurance Co. Ltd",
	"APA Insurance Ltd",
	"Britam General Insurance Co. Ltd",
	"Cannon General Insurance Ltd",
	"CIC General Insurance Ltd",
	"Corporate Insurance Co. Ltd",
	"DirectLine Assurance Co. Ltd",
	"Fidelity Shield Insurance Co. Ltd",
	"First Assurance Co. Ltd",
	"GA Insurance Ltd",
	"Geminia Insurance Co. Ltd",
	"Heritage Insurance Co. Ltd",
	"Intra Africa Assurance Co. Ltd",
	"Jubilee General Insurance Ltd",
	"Kenindia Assurance Co. Ltd",
	"Kenya Orient Insurance Ltd",
	"Madison General Insurance Kenya Ltd",
	"Mayfair Insurance Co. Ltd",
	"Occidental Insurance Co. Ltd",
	"Pacis Insurance Co. Ltd",
	"Resolution Insurance Ltd",
	"Sanlam General Insurance Ltd",
	"Takaful Insurance of Africa Ltd",
	"Tausi Assurance Co. Ltd",
	"Trident Insurance Co. Ltd",
	"UAP Old Mutual General Insurance Ltd",
	"Xplico Insurance Co. Ltd",
	"Monarch Insurance Co. Ltd",
	"Saham Assurance Co. Ltd",
	"Continental Insurance Co. Ltd",
	"Pioneer General Insurance Ltd",
	"Prudential Assurance Kenya Ltd",
	"Amaco Insurance Ltd"
]

# Regulatory bodies data
REGULATORY_BODIES = [
	"Insurance Regulatory Authority (IRA)",
	"National Transport and Safety Authority (NTSA)"
]

with app.app_context():
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
		
		# Populate insurance companies if not exists
		if InsuranceCompany.query.count() == 0:
			for company_name in INSURANCE_COMPANIES:
				company = InsuranceCompany(name=company_name)
				db.session.add(company)
			db.session.commit()
			print(f"Added {len(INSURANCE_COMPANIES)} insurance companies to database")
		
		# Populate regulatory bodies if not exists
		if RegulatoryBody.query.count() == 0:
			for body_name in REGULATORY_BODIES:
				body = RegulatoryBody(name=body_name)
				db.session.add(body)
			db.session.commit()
			print(f"Added {len(REGULATORY_BODIES)} regulatory bodies to database")
			
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
			# Insurers need to be approved, so is_approved=False by default
			user = Insurer(username=username, email=email, password=hashed_password, staff_id=None, is_approved=False)
		elif user_type == 'regulator':
			# Regulators need to be approved, so is_approved=False by default
			user = Regulator(username=username, email=email, password=hashed_password, staff_id=None, is_approved=False)
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
	pending_insurer_count = InsurerRequest.query.filter_by(status='pending').count()
	pending_regulator_count = RegulatorRequest.query.filter_by(status='pending').count()
	
	return render_template('admin/admindashboard.html', 
						   customers=customers, 
						   insurers=insurers, 
						   regulators=regulators,
						   pending_count=pending_insurer_count,
						   pending_regulator_count=pending_regulator_count)

@app.route('/admin/search')
@login_required
@admin_required
def admin_search():
	return render_template('admin/search.html')

@app.route('/admin/insurer-requests')
@login_required
@admin_required
def review_insurer_requests():
	pending_requests = InsurerRequest.query.filter_by(status='pending').order_by(InsurerRequest.request_date.desc()).all()
	approved_requests = InsurerRequest.query.filter_by(status='approved').order_by(InsurerRequest.reviewed_date.desc()).all()
	rejected_requests = InsurerRequest.query.filter_by(status='rejected').order_by(InsurerRequest.reviewed_date.desc()).all()
	
	return render_template('admin/review_requests.html',
						   pending_requests=pending_requests,
						   approved_requests=approved_requests,
						   rejected_requests=rejected_requests)

@app.route('/admin/approve-request/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def approve_insurer_request(request_id):
	access_request = InsurerRequest.query.get_or_404(request_id)
	
	if access_request.status != 'pending':
		flash('This request has already been reviewed.', 'warning')
		return redirect(url_for('review_insurer_requests'))
	
	# Update request status
	access_request.status = 'approved'
	access_request.reviewed_date = datetime.utcnow()
	access_request.reviewed_by = current_user.id
	
	# Update insurer record
	insurer = access_request.insurer
	insurer.is_approved = True
	insurer.staff_id = access_request.staff_id
	insurer.insurance_company_id = access_request.insurance_company_id
	insurer.approval_date = datetime.utcnow()
	
	db.session.commit()
	
	flash(f'Access request for {insurer.username} has been approved.', 'success')
	return redirect(url_for('review_insurer_requests'))

@app.route('/admin/reject-request/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def reject_insurer_request(request_id):
	access_request = InsurerRequest.query.get_or_404(request_id)
	
	if access_request.status != 'pending':
		flash('This request has already been reviewed.', 'warning')
		return redirect(url_for('review_insurer_requests'))
	
	rejection_reason = request.form.get('rejection_reason', 'No reason provided')
	
	# Update request status
	access_request.status = 'rejected'
	access_request.reviewed_date = datetime.utcnow()
	access_request.reviewed_by = current_user.id
	access_request.rejection_reason = rejection_reason
	
	db.session.commit()
	
	flash(f'Access request for {access_request.insurer.username} has been rejected.', 'info')
	return redirect(url_for('review_insurer_requests'))

@app.route('/admin/regulator-requests')
@login_required
@admin_required
def review_regulator_requests():
	pending_requests = RegulatorRequest.query.filter_by(status='pending').order_by(RegulatorRequest.request_date.desc()).all()
	approved_requests = RegulatorRequest.query.filter_by(status='approved').order_by(RegulatorRequest.reviewed_date.desc()).all()
	rejected_requests = RegulatorRequest.query.filter_by(status='rejected').order_by(RegulatorRequest.reviewed_date.desc()).all()
	
	return render_template('admin/review_regulator_requests.html',
						   pending_requests=pending_requests,
						   approved_requests=approved_requests,
						   rejected_requests=rejected_requests)

@app.route('/admin/approve-regulator-request/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def approve_regulator_request(request_id):
	access_request = RegulatorRequest.query.get_or_404(request_id)
	
	if access_request.status != 'pending':
		flash('This request has already been reviewed.', 'warning')
		return redirect(url_for('review_regulator_requests'))
	
	# Update request status
	access_request.status = 'approved'
	access_request.reviewed_date = datetime.utcnow()
	access_request.reviewed_by = current_user.id
	
	# Update regulator record
	regulator = access_request.regulator
	regulator.is_approved = True
	regulator.staff_id = access_request.staff_id
	regulator.regulatory_body_id = access_request.regulatory_body_id
	regulator.approval_date = datetime.utcnow()
	
	db.session.commit()
	
	flash(f'Access request for {regulator.username} has been approved.', 'success')
	return redirect(url_for('review_regulator_requests'))

@app.route('/admin/reject-regulator-request/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def reject_regulator_request(request_id):
	access_request = RegulatorRequest.query.get_or_404(request_id)
	
	if access_request.status != 'pending':
		flash('This request has already been reviewed.', 'warning')
		return redirect(url_for('review_regulator_requests'))
	
	rejection_reason = request.form.get('rejection_reason', 'No reason provided')
	
	# Update request status
	access_request.status = 'rejected'
	access_request.reviewed_date = datetime.utcnow()
	access_request.reviewed_by = current_user.id
	access_request.rejection_reason = rejection_reason
	
	db.session.commit()
	
	flash(f'Access request for {access_request.regulator.username} has been rejected.', 'info')
	return redirect(url_for('review_regulator_requests'))

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

@app.route('/customer/search')
@login_required
@customer_required
def customer_search():
	return render_template('customer/search.html')

@app.route('/insurer/dashboard')
@login_required
@insurer_required
def insurer_dashboard():
	# Check if insurer is approved
	if not current_user.is_approved:
		# Check if they have a pending request
		pending_request = InsurerRequest.query.filter_by(
			insurer_id=current_user.id,
			status='pending'
		).first()
		
		if pending_request:
			return render_template('insurer/pending_approval.html', request=pending_request)
		else:
			# No request yet, redirect to request access page
			return redirect(url_for('request_insurer_access'))
	
	# Get dashboard statistics
	company_id = current_user.insurance_company_id
	
	# Total policies
	total_policies = Policy.query.filter_by(insurance_company_id=company_id).count()
	
	# Active policies (not expired)
	active_policies = Policy.query.filter_by(insurance_company_id=company_id).filter(
		Policy.expiry_date >= datetime.now().date()
	).count()
	
	# Recent policies (last 5)
	recent_policies = Policy.query.filter_by(insurance_company_id=company_id).order_by(
		Policy.date_entered.desc()
	).limit(5).all()
	
	# Calculate total premium for active policies
	total_premium = db.session.query(db.func.sum(Policy.premium_amount)).filter(
		Policy.insurance_company_id == company_id,
		Policy.expiry_date >= datetime.now().date()
	).scalar() or 0
	
	# Insurer is approved, show dashboard with data
	return render_template('insurer/insurerdashboard.html',
						   total_policies=total_policies,
						   active_policies=active_policies,
						   recent_policies=recent_policies,
						   total_premium=total_premium,
						   now=datetime.now())

@app.route('/insurer/search')
@login_required
@insurer_required
def insurer_search():
	return render_template('insurer/search.html')

@app.route('/insurer/create-policy', methods=['GET', 'POST'])
@login_required
@insurer_required
def create_policy():
	# Ensure insurer is approved
	if not current_user.is_approved:
		flash('You must be approved to create policies.', 'warning')
		return redirect(url_for('insurer_dashboard'))
	
	form = PolicyCreationForm()
	
	if form.validate_on_submit():
		# Generate policy number based on policy type
		policy_type = form.policy_type.data
		prefix = 'CO' if policy_type == 'Comprehensive' else 'TO'
		
		# Get the latest policy number for this type
		last_policy = Policy.query.filter(
			Policy.policy_number.like(f'{prefix}-%')
		).order_by(Policy.id.desc()).first()
		
		if last_policy:
			# Extract number and increment
			last_num = int(last_policy.policy_number.split('-')[1])
			new_num = last_num + 1
		else:
			new_num = 1
		
		policy_number = f'{prefix}-{str(new_num).zfill(4)}'
		
		# Calculate expiry date (1 year from effective date)
		effective_date = form.effective_date.data
		expiry_date = effective_date.replace(year=effective_date.year + 1)
		
		# Create new policy
		new_policy = Policy(
			policy_number=policy_number,
			policy_type=policy_type,
			effective_date=effective_date,
			expiry_date=expiry_date,
			premium_amount=form.premium_amount.data,
			payment_mode=form.payment_mode.data,
			insured_name=form.insured_name.data,
			national_id=form.national_id.data,
			kra_pin=form.kra_pin.data if form.kra_pin.data else None,
			date_of_birth=form.date_of_birth.data,
			phone_number=form.phone_number.data,
			email_address=form.email_address.data,
			postal_address=form.postal_address.data,
			registration_number=form.registration_number.data.upper(),
			make_model=form.make_model.data,
			year_of_manufacture=form.year_of_manufacture.data,
			body_type=form.body_type.data,
			color=form.color.data,
			chassis_number=form.chassis_number.data,
			engine_number=form.engine_number.data,
			seating_capacity=form.seating_capacity.data,
			use_category=form.use_category.data,
			sum_insured=form.sum_insured.data,
			excess=form.excess.data,
			political_violence=form.political_violence.data,
			windscreen_cover=form.windscreen_cover.data,
			passenger_liability=form.passenger_liability.data,
			road_rescue=form.road_rescue.data,
			insurance_company_id=current_user.insurance_company_id,
			created_by=current_user.id
		)
		
		db.session.add(new_policy)
		db.session.commit()
		
		# Handle photo uploads
		photo_types = [
			'front_view', 'left_side', 'right_side', 'rear_view', 
			'engine_bay', 'underneath', 'roof', 'instrument_cluster',
			'front_interior', 'back_interior', 'boot_trunk'
		]
		
		# Create upload directory for this policy
		upload_dir = os.path.join(app.root_path, 'upload', 'insurer', str(new_policy.id))
		os.makedirs(upload_dir, exist_ok=True)
		
		# Save each photo
		for photo_type in photo_types:
			if photo_type in request.files:
				file = request.files[photo_type]
				if file and file.filename:
					# Secure filename and save
					filename = secure_filename(f"{photo_type}_{file.filename}")
					file_path = os.path.join(upload_dir, filename)
					file.save(file_path)
					
					# Save photo record to database (path relative to upload directory)
					relative_path = os.path.join('insurer', str(new_policy.id), filename)
					photo = PolicyPhoto(
						policy_id=new_policy.id,
						photo_type=photo_type,
						file_path=relative_path
					)
					db.session.add(photo)
		
		db.session.commit()
		
		flash(f'Policy {policy_number} created successfully!', 'success')
		return redirect(url_for('insurer_dashboard'))
	
	return render_template('insurer/create_policy.html', form=form)

@app.route('/insurer/upload-photo/<int:policy_id>', methods=['POST'])
@login_required
@insurer_required
def upload_photo(policy_id):
	"""AJAX endpoint for uploading policy photos"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Verify policy belongs to insurer's company
	if policy.insurance_company_id != current_user.insurance_company_id:
		return jsonify({'success': False, 'error': 'Unauthorized'}), 403
	
	if 'photo' not in request.files:
		return jsonify({'success': False, 'error': 'No photo provided'}), 400
	
	file = request.files['photo']
	photo_type = request.form.get('photo_type')
	
	if file.filename == '':
		return jsonify({'success': False, 'error': 'No file selected'}), 400
	
	if not photo_type:
		return jsonify({'success': False, 'error': 'Photo type not specified'}), 400
	
	# Create upload directory for this policy
	upload_dir = os.path.join(app.root_path, 'upload', 'insurer', str(policy_id))
	os.makedirs(upload_dir, exist_ok=True)
	
	# Secure filename and save
	filename = secure_filename(f"{photo_type}_{file.filename}")
	file_path = os.path.join(upload_dir, filename)
	file.save(file_path)
	
	# Save photo record to database (path relative to upload directory)
	relative_path = os.path.join('insurer', str(policy_id), filename)
	photo = PolicyPhoto(
		policy_id=policy_id,
		photo_type=photo_type,
		file_path=relative_path
	)
	db.session.add(photo)
	db.session.commit()
	
	return jsonify({
		'success': True,
		'photo_id': photo.id,
		'file_path': relative_path
	})

@app.route('/insurer/manage-policies')
@login_required
@insurer_required
def manage_policies():
	"""View and manage all policies created by the insurer's company"""
	# Ensure insurer is approved
	if not current_user.is_approved:
		flash('You must be approved to manage policies.', 'warning')
		return redirect(url_for('insurer_dashboard'))
	
	# Get filter parameters
	search_query = request.args.get('search', '')
	policy_type_filter = request.args.get('policy_type', '')
	status_filter = request.args.get('status', 'all')
	
	# Base query - get all policies from insurer's company
	policies_query = Policy.query.filter_by(insurance_company_id=current_user.insurance_company_id)
	
	# Apply search filter
	if search_query:
		search_pattern = f"%{search_query}%"
		policies_query = policies_query.filter(
			db.or_(
				Policy.policy_number.ilike(search_pattern),
				Policy.insured_name.ilike(search_pattern),
				Policy.registration_number.ilike(search_pattern),
				Policy.national_id.ilike(search_pattern)
			)
		)
	
	# Apply policy type filter
	if policy_type_filter:
		policies_query = policies_query.filter_by(policy_type=policy_type_filter)
	
	# Apply status filter (active/expired)
	if status_filter == 'active':
		policies_query = policies_query.filter(Policy.expiry_date >= datetime.now().date())
	elif status_filter == 'expired':
		policies_query = policies_query.filter(Policy.expiry_date < datetime.now().date())
	
	# Order by creation date (newest first)
	policies = policies_query.order_by(Policy.date_entered.desc()).all()
	
	# Calculate statistics
	total_policies = Policy.query.filter_by(insurance_company_id=current_user.insurance_company_id).count()
	active_policies = Policy.query.filter_by(insurance_company_id=current_user.insurance_company_id).filter(
		Policy.expiry_date >= datetime.now().date()
	).count()
	expired_policies = total_policies - active_policies
	
	return render_template('insurer/manage_policies.html', 
						   policies=policies,
						   search_query=search_query,
						   policy_type_filter=policy_type_filter,
						   status_filter=status_filter,
						   total_policies=total_policies,
						   active_policies=active_policies,
						   expired_policies=expired_policies,
						   now=datetime.now())

@app.route('/insurer/policy/<int:policy_id>')
@login_required
@insurer_required
def view_policy(policy_id):
	"""View detailed information about a specific policy"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Verify policy belongs to insurer's company
	if policy.insurance_company_id != current_user.insurance_company_id:
		flash('You do not have permission to view this policy.', 'danger')
		return redirect(url_for('manage_policies'))
	
	# Get policy photos
	photos = PolicyPhoto.query.filter_by(policy_id=policy_id).all()
	
	# Get policy creator information
	creator = Insurer.query.get(policy.created_by)
	
	# Check if policy is active
	is_active = policy.expiry_date >= datetime.now().date()
	
	return render_template('insurer/view_policy.html', 
						   policy=policy,
						   photos=photos,
						   creator=creator,
						   is_active=is_active)

@app.route('/insurer/request-access', methods=['GET', 'POST'])
@login_required
@insurer_required
def request_insurer_access():
	# Check if already approved
	if current_user.is_approved:
		return redirect(url_for('insurer_dashboard'))
	
	# Check if there's already a pending request
	existing_request = InsurerRequest.query.filter_by(
		insurer_id=current_user.id,
		status='pending'
	).first()
	
	if existing_request:
		return render_template('insurer/pending_approval.html', request=existing_request)
	
	form = InsurerAccessRequestForm()
	
	# Populate insurance company choices
	companies = InsuranceCompany.query.filter_by(is_active=True).order_by(InsuranceCompany.name).all()
	form.insurance_company.choices = [(c.id, c.name) for c in companies]
	
	if form.validate_on_submit():
		staff_id = form.staff_id.data
		insurance_company_id = form.insurance_company.data
		
		# Create access request
		access_request = InsurerRequest(
			insurer_id=current_user.id,
			staff_id=staff_id,
			insurance_company_id=insurance_company_id,
			status='pending'
		)
		
		db.session.add(access_request)
		db.session.commit()
		
		flash('Your access request has been submitted. Please wait for admin approval.', 'success')
		return redirect(url_for('insurer_dashboard'))
	
	return render_template('insurer/request_access.html', form=form)

@app.route('/regulator/dashboard')
@login_required
@regulator_required
def regulator_dashboard():
	# Check if regulator is approved
	if not current_user.is_approved:
		# Check if they have a pending request
		pending_request = RegulatorRequest.query.filter_by(
			regulator_id=current_user.id,
			status='pending'
		).first()
		
		if pending_request:
			return render_template('regulator/pending_approval.html', request=pending_request)
		else:
			# No request yet, redirect to request access page
			return redirect(url_for('request_regulator_access'))
	
	# Regulator is approved, show dashboard
	return render_template('regulator/regulatordashboard.html')

@app.route('/regulator/request-access', methods=['GET', 'POST'])
@login_required
@regulator_required
def request_regulator_access():
	# Check if already approved
	if current_user.is_approved:
		return redirect(url_for('regulator_dashboard'))
	
	# Check if there's already a pending request
	existing_request = RegulatorRequest.query.filter_by(
		regulator_id=current_user.id,
		status='pending'
	).first()
	
	if existing_request:
		return render_template('regulator/pending_approval.html', request=existing_request)
	
	form = RegulatorAccessRequestForm()
	
	# Populate regulatory body choices
	bodies = RegulatoryBody.query.filter_by(is_active=True).order_by(RegulatoryBody.name).all()
	form.regulatory_body.choices = [(b.id, b.name) for b in bodies]
	
	if form.validate_on_submit():
		staff_id = form.staff_id.data
		regulatory_body_id = form.regulatory_body.data
		
		# Create access request
		access_request = RegulatorRequest(
			regulator_id=current_user.id,
			staff_id=staff_id,
			regulatory_body_id=regulatory_body_id,
			status='pending'
		)
		
		db.session.add(access_request)
		db.session.commit()
		
		flash('Your access request has been submitted. Please wait for admin approval.', 'success')
		return redirect(url_for('regulator_dashboard'))
	
	return render_template('regulator/request_access.html', form=form)

@app.route('/regulator/search')
@login_required
@regulator_required
def regulator_search():
	return render_template('regulator/search.html')

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
	"""Serve uploaded files"""
	return send_from_directory(os.path.join(app.root_path, 'upload'), filename)

if __name__ == '__main__':
	app.run(debug=True)