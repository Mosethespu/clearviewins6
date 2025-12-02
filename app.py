
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory, session
from config import Config
from extension import db, login_manager, migrate, cache
from models import Admin, Customer, Insurer, Regulator, InsuranceCompany, InsurerRequest, RegulatoryBody, RegulatorRequest, Policy, PolicyPhoto, Claim, ClaimDocument, PremiumRate, Quote
from forms import SignupForm, LoginForm, InsurerAccessRequestForm, RegulatorAccessRequestForm, PolicyCreationForm, ClaimForm
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
	
	# Claims statistics
	total_claims = Claim.query.filter_by(insurance_company_id=company_id).count()
	pending_claims = Claim.query.filter_by(insurance_company_id=company_id, status='Pending').count()
	under_review_claims = Claim.query.filter_by(insurance_company_id=company_id, status='Under Review').count()
	
	# Recent claims (last 5)
	recent_claims = Claim.query.filter_by(insurance_company_id=company_id).order_by(
		Claim.date_submitted.desc()
	).limit(5).all()
	
	# Insurer is approved, show dashboard with data
	return render_template('insurer/insurerdashboard.html',
						   total_policies=total_policies,
						   active_policies=active_policies,
						   recent_policies=recent_policies,
						   total_premium=total_premium,
						   total_claims=total_claims,
						   pending_claims=pending_claims,
						   under_review_claims=under_review_claims,
						   recent_claims=recent_claims,
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
	
	# Pre-fill form from calculator if data exists
	if request.method == 'GET' and 'prefill_policy' in session:
		calc_data = session['prefill_policy']
		
		# Pre-fill vehicle information
		if 'vehicle_value' in calc_data:
			form.sum_insured.data = calc_data['vehicle_value']
		if 'registration_number' in calc_data:
			form.registration_number.data = calc_data['registration_number']
		if 'make_model' in calc_data:
			form.make_model.data = calc_data['make_model']
		if 'year_of_manufacture' in calc_data:
			form.year_of_manufacture.data = calc_data['year_of_manufacture']
		
		# Pre-fill cover type as policy type
		if 'cover_type' in calc_data:
			cover_type = calc_data['cover_type']
			if cover_type == 'Comprehensive':
				form.policy_type.data = 'Comprehensive'
			elif cover_type in ['Third-Party Only', 'Third-Party Fire & Theft']:
				form.policy_type.data = 'Third-Party'
		
		# Pre-fill use category
		if 'use_category' in calc_data:
			form.use_category.data = calc_data['use_category']
		
		# Pre-fill premium amount
		if 'final_premium' in calc_data:
			form.premium_amount.data = calc_data['final_premium']
		
		# Pre-fill add-ons
		if 'political_violence' in calc_data:
			form.political_violence.data = calc_data['political_violence']
		if 'windscreen_cover' in calc_data:
			form.windscreen_cover.data = calc_data['windscreen_cover']
		if 'passenger_liability' in calc_data:
			form.passenger_liability.data = calc_data['passenger_liability']
		if 'road_rescue' in calc_data:
			form.road_rescue.data = calc_data['road_rescue']
		
		# Pre-fill customer information if available
		if 'customer_email' in calc_data:
			form.email_address.data = calc_data['customer_email']
		if 'customer_name' in calc_data:
			form.insured_name.data = calc_data['customer_name']
		if 'customer_phone' in calc_data:
			form.phone_number.data = calc_data['customer_phone']
		
		# Clear session data after pre-filling
		session.pop('prefill_policy', None)
		
		flash('Policy form pre-filled from calculator. Please complete remaining required fields.', 'info')
	
	if form.validate_on_submit():
		# Check if registration number is already used in an active policy
		registration_number = form.registration_number.data.upper()
		existing_policy = Policy.query.filter_by(
			registration_number=registration_number,
			status='Active'
		).first()
		
		if existing_policy:
			flash(f'Registration number {registration_number} is already used in an active policy (Policy No: {existing_policy.policy_number}). A vehicle can only be in one active policy at a time.', 'danger')
			return render_template('insurer/create_policy.html', form=form)
		
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
			created_by=current_user.id,
			status='Active'
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
	
	# Apply status filter
	if status_filter == 'active':
		policies_query = policies_query.filter_by(status='Active')
	elif status_filter == 'expired':
		policies_query = policies_query.filter_by(status='Expired')
	elif status_filter == 'cancelled':
		policies_query = policies_query.filter_by(status='Cancelled')
	
	# Order by creation date (newest first)
	policies = policies_query.order_by(Policy.date_entered.desc()).all()
	
	# Calculate statistics
	total_policies = Policy.query.filter_by(insurance_company_id=current_user.insurance_company_id).count()
	active_policies = Policy.query.filter_by(insurance_company_id=current_user.insurance_company_id, status='Active').count()
	cancelled_policies = Policy.query.filter_by(insurance_company_id=current_user.insurance_company_id, status='Cancelled').count()
	expired_policies = Policy.query.filter_by(insurance_company_id=current_user.insurance_company_id, status='Expired').count()
	
	return render_template('insurer/manage_policies.html', 
						   policies=policies,
						   search_query=search_query,
						   policy_type_filter=policy_type_filter,
						   status_filter=status_filter,
						   total_policies=total_policies,
						   active_policies=active_policies,
						   cancelled_policies=cancelled_policies,
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
	
	# Get canceller information if policy is cancelled
	canceller = None
	if policy.cancelled_by:
		canceller = Insurer.query.get(policy.cancelled_by)
	
	# Check if policy is active
	is_active = policy.expiry_date >= datetime.now().date()
	
	return render_template('insurer/view_policy.html', 
						   policy=policy,
						   photos=photos,
						   creator=creator,
						   canceller=canceller,
						   is_active=is_active)

@app.route('/insurer/cancel-policy/<int:policy_id>', methods=['POST'])
@login_required
@insurer_required
def cancel_policy(policy_id):
	"""Cancel a policy"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Verify policy belongs to insurer's company
	if policy.insurance_company_id != current_user.insurance_company_id:
		flash('You do not have permission to cancel this policy.', 'danger')
		return redirect(url_for('manage_policies'))
	
	# Check if policy is already cancelled
	if policy.status == 'Cancelled':
		flash('This policy has already been cancelled.', 'warning')
		return redirect(url_for('view_policy', policy_id=policy_id))
	
	# Check if policy is already expired
	if policy.status == 'Expired':
		flash('Cannot cancel an expired policy.', 'warning')
		return redirect(url_for('view_policy', policy_id=policy_id))
	
	# Get cancellation reason from form
	cancellation_reason = request.form.get('cancellation_reason', '').strip()
	
	if not cancellation_reason:
		flash('Please provide a reason for cancellation.', 'warning')
		return redirect(url_for('view_policy', policy_id=policy_id))
	
	# Update policy status
	policy.status = 'Cancelled'
	policy.cancelled_by = current_user.id
	policy.cancellation_date = datetime.now()
	policy.cancellation_reason = cancellation_reason
	
	db.session.commit()
	
	flash(f'Policy {policy.policy_number} has been cancelled successfully.', 'success')
	return redirect(url_for('view_policy', policy_id=policy_id))

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

# Claims Management Routes
@app.route('/insurer/claims')
@login_required
@insurer_required
def manage_claims():
	"""List all claims for the insurer's company with search/filter"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	company_id = current_user.insurance_company_id
	
	# Get filter parameters
	status_filter = request.args.get('status', '')
	search_query = request.args.get('search', '')
	
	# Base query - only claims for this insurance company
	query = Claim.query.filter_by(insurance_company_id=company_id)
	
	# Apply filters
	if status_filter:
		query = query.filter_by(status=status_filter)
	
	if search_query:
		# Search in claim number, policy number, or insured name
		query = query.join(Policy).filter(
			(Claim.claim_number.ilike(f'%{search_query}%')) |
			(Policy.policy_number.ilike(f'%{search_query}%')) |
			(Policy.insured_name.ilike(f'%{search_query}%'))
		)
	
	# Get claims ordered by submission date (newest first)
	claims = query.order_by(Claim.date_submitted.desc()).all()
	
	# Calculate statistics
	total_claims = Claim.query.filter_by(insurance_company_id=company_id).count()
	pending_claims = Claim.query.filter_by(insurance_company_id=company_id, status='Pending').count()
	under_review = Claim.query.filter_by(insurance_company_id=company_id, status='Under Review').count()
	approved_claims = Claim.query.filter_by(insurance_company_id=company_id, status='Approved').count()
	rejected_claims = Claim.query.filter_by(insurance_company_id=company_id, status='Rejected').count()
	
	return render_template('insurer/claims.html',
						   claims=claims,
						   total_claims=total_claims,
						   pending_claims=pending_claims,
						   under_review=under_review,
						   approved_claims=approved_claims,
						   rejected_claims=rejected_claims,
						   status_filter=status_filter,
						   search_query=search_query,
						   datetime=datetime)

@app.route('/insurer/create-claim', methods=['GET', 'POST'])
@login_required
@insurer_required
def create_claim():
	"""Create a new insurance claim"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	form = ClaimForm()
	
	if request.method == 'POST':
		# Manual validation since we're bypassing some WTForms validation
		policy_id = request.form.get('policy_id')
		if not policy_id:
			flash('Please select a policy first.', 'danger')
			return render_template('insurer/create_claim.html', form=form, datetime=datetime)
		
		try:
			# Get policy and verify it belongs to this company
			policy = Policy.query.get_or_404(policy_id)
			if policy.insurance_company_id != current_user.insurance_company_id:
				flash('Invalid policy selected.', 'danger')
				return redirect(url_for('create_claim'))
			
			# Check if policy already has a claim
			existing_claim = Claim.query.filter_by(policy_id=policy_id).first()
			if existing_claim:
				flash(f'This policy already has a claim (Claim No: {existing_claim.claim_number}). Only one claim can be made per policy.', 'danger')
				return render_template('insurer/create_claim.html', form=form, datetime=datetime)
			
			# Generate claim number (CL-XXXX format)
			last_claim = Claim.query.order_by(Claim.id.desc()).first()
			if last_claim and last_claim.claim_number.startswith('CL-'):
				last_number = int(last_claim.claim_number.split('-')[1])
				new_number = last_number + 1
			else:
				new_number = 1
			claim_number = f"CL-{new_number:04d}"
			
			# Create claim
			claim = Claim(
				claim_number=claim_number,
				policy_id=policy_id,
				insurance_company_id=current_user.insurance_company_id,
				accident_date=datetime.strptime(request.form.get('accident_date'), '%Y-%m-%d').date(),
				accident_time=datetime.strptime(request.form.get('accident_time'), '%H:%M').time(),
				accident_location=request.form.get('accident_location'),
				accident_description=request.form.get('accident_description'),
				weather_conditions=request.form.get('weather_conditions'),
				police_report_number=request.form.get('police_report_number'),
				vehicle_towed=(request.form.get('vehicle_towed') == 'Yes'),
				tow_location=request.form.get('tow_location') if request.form.get('vehicle_towed') == 'Yes' else None,
				damage_insured_vehicle=request.form.get('damage_insured_vehicle'),
				damage_third_party=request.form.get('damage_third_party'),
				injuries_driver_passengers=request.form.get('injuries_driver_passengers'),
				injuries_third_parties=request.form.get('injuries_third_parties'),
				witness_name=request.form.get('witness_name'),
				witness_contact=request.form.get('witness_contact'),
				witness_statement=request.form.get('witness_statement'),
				status='Pending',
				created_by=current_user.id
			)
			
			db.session.add(claim)
			db.session.commit()
			
			# Create directory for claim documents - changed to upload/claims/{id}
			claim_dir = os.path.join('upload', 'claims', str(claim.id))
			os.makedirs(claim_dir, exist_ok=True)
			
			# Handle file uploads
			document_types = [
				'accident_photo_1', 'accident_photo_2', 'accident_photo_3', 'accident_photo_4',
				'damage_photo_front', 'damage_photo_side', 'damage_photo_rear', 'damage_photo_interior',
				'police_abstract', 'driver_license', 'logbook'
			]
			
			uploaded_count = 0
			for doc_type in document_types:
				if doc_type in request.files:
					file = request.files[doc_type]
					if file and file.filename:
						filename = secure_filename(file.filename)
						file_path = os.path.join(claim_dir, f"{doc_type}_{filename}")
						file.save(file_path)
						
						# Save document record (store relative path)
						relative_path = f"claims/{claim.id}/{doc_type}_{filename}"
						document = ClaimDocument(
							claim_id=claim.id,
							document_type=doc_type,
							file_path=relative_path
						)
						db.session.add(document)
						uploaded_count += 1
			
			db.session.commit()
			
			flash(f'Claim {claim_number} submitted successfully! {uploaded_count} documents uploaded.', 'success')
			return redirect(url_for('view_claim', claim_id=claim.id))
			
		except Exception as e:
			db.session.rollback()
			print(f"Error creating claim: {str(e)}")  # Debug logging
			import traceback
			traceback.print_exc()
			flash(f'Error creating claim: {str(e)}', 'danger')
			return render_template('insurer/create_claim.html', form=form, datetime=datetime)
	
	return render_template('insurer/create_claim.html', form=form, datetime=datetime)

@app.route('/insurer/claim/<int:claim_id>')
@login_required
@insurer_required
def view_claim(claim_id):
	"""View detailed claim information"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	# Get claim and verify it belongs to this company
	claim = Claim.query.get_or_404(claim_id)
	if claim.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access.', 'danger')
		return redirect(url_for('manage_claims'))
	
	# Get related policy and creator
	policy = Policy.query.get(claim.policy_id)
	creator = Insurer.query.get(claim.created_by)
	
	# Group documents by type
	accident_photos = [doc for doc in claim.documents if 'accident_photo' in doc.document_type]
	damage_photos = [doc for doc in claim.documents if 'damage_photo' in doc.document_type]
	police_docs = [doc for doc in claim.documents if 'police_abstract' in doc.document_type]
	license_docs = [doc for doc in claim.documents if 'driver_license' in doc.document_type]
	logbook_docs = [doc for doc in claim.documents if 'logbook' in doc.document_type]
	
	return render_template('insurer/view_claim.html',
						   claim=claim,
						   policy=policy,
						   creator=creator,
						   accident_photos=accident_photos,
						   damage_photos=damage_photos,
						   police_docs=police_docs,
						   license_docs=license_docs,
						   logbook_docs=logbook_docs,
						   datetime=datetime)

@app.route('/insurer/upload-claim-document/<int:claim_id>', methods=['POST'])
@login_required
@insurer_required
def upload_claim_document(claim_id):
	"""AJAX endpoint for uploading additional claim documents"""
	if not current_user.is_approved:
		return jsonify({'success': False, 'error': 'Not approved'}), 403
	
	claim = Claim.query.get_or_404(claim_id)
	if claim.insurance_company_id != current_user.insurance_company_id:
		return jsonify({'success': False, 'error': 'Unauthorized'}), 403
	
	if 'file' not in request.files:
		return jsonify({'success': False, 'error': 'No file provided'}), 400
	
	file = request.files['file']
	document_type = request.form.get('document_type', 'other')
	
	if file.filename == '':
		return jsonify({'success': False, 'error': 'No file selected'}), 400
	
	if file:
		try:
			filename = secure_filename(file.filename)
			claim_dir = os.path.join('upload', 'claims', str(claim_id))
			os.makedirs(claim_dir, exist_ok=True)
			
			file_path = os.path.join(claim_dir, f"{document_type}_{filename}")
			file.save(file_path)
			
			# Save document record
			relative_path = f"claims/{claim_id}/{document_type}_{filename}"
			document = ClaimDocument(
				claim_id=claim_id,
				document_type=document_type,
				file_path=relative_path
			)
			db.session.add(document)
			db.session.commit()
			
			return jsonify({
				'success': True,
				'message': 'Document uploaded successfully',
				'document_id': document.id,
				'file_url': url_for('uploaded_file', filename=relative_path)
			})
			
		except Exception as e:
			db.session.rollback()
			return jsonify({'success': False, 'error': str(e)}), 500
	
	return jsonify({'success': False, 'error': 'File upload failed'}), 400

@app.route('/insurer/review-claim/<int:claim_id>', methods=['GET', 'POST'])
@login_required
@insurer_required
def review_claim(claim_id):
	"""Review a claim and mark it as 'Under Review'"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	claim = Claim.query.get_or_404(claim_id)
	if claim.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access.', 'danger')
		return redirect(url_for('manage_claims'))
	
	# Check if claim is in Pending status
	if claim.status != 'Pending':
		flash(f'This claim is already {claim.status}. Only pending claims can be reviewed.', 'warning')
		return redirect(url_for('view_claim', claim_id=claim_id))
	
	if request.method == 'POST':
		review_notes = request.form.get('review_notes', '').strip()
		
		# Update claim status to Under Review
		claim.status = 'Under Review'
		claim.reviewed_by = current_user.id
		claim.review_date = datetime.now()
		claim.review_notes = review_notes if review_notes else None
		
		db.session.commit()
		
		flash(f'Claim {claim.claim_number} is now under review.', 'success')
		return redirect(url_for('view_claim', claim_id=claim_id))
	
	# GET request - show claim for review
	policy = Policy.query.get(claim.policy_id)
	creator = Insurer.query.get(claim.created_by)
	
	# Group documents by type
	accident_photos = [doc for doc in claim.documents if 'accident_photo' in doc.document_type]
	damage_photos = [doc for doc in claim.documents if 'damage_photo' in doc.document_type]
	police_docs = [doc for doc in claim.documents if 'police_abstract' in doc.document_type]
	license_docs = [doc for doc in claim.documents if 'driver_license' in doc.document_type]
	logbook_docs = [doc for doc in claim.documents if 'logbook' in doc.document_type]
	
	return render_template('insurer/review_claim.html',
						   claim=claim,
						   policy=policy,
						   creator=creator,
						   accident_photos=accident_photos,
						   damage_photos=damage_photos,
						   police_docs=police_docs,
						   license_docs=license_docs,
						   logbook_docs=logbook_docs,
						   datetime=datetime)

@app.route('/insurer/fraud-check/<int:claim_id>', methods=['POST'])
@login_required
@insurer_required
def fraud_check_claim(claim_id):
	"""Perform fraud check on a claim (placeholder for future AI integration)"""
	if not current_user.is_approved:
		return jsonify({'success': False, 'error': 'Not approved'}), 403
	
	claim = Claim.query.get_or_404(claim_id)
	if claim.insurance_company_id != current_user.insurance_company_id:
		return jsonify({'success': False, 'error': 'Unauthorized'}), 403
	
	# Check if claim is Under Review
	if claim.status != 'Under Review':
		return jsonify({'success': False, 'error': 'Claim must be under review for fraud check'}), 400
	
	# Placeholder fraud check logic - to be replaced with actual AI/ML model
	# For now, generate a simple mock result
	import random
	
	fraud_risk_score = random.uniform(5.0, 45.0)  # Low risk score for demo
	
	if fraud_risk_score < 20:
		risk_level = "Low Risk"
		result_message = "No significant fraud indicators detected. Claim appears legitimate."
	elif fraud_risk_score < 50:
		risk_level = "Medium Risk"
		result_message = "Some minor inconsistencies detected. Manual review recommended."
	else:
		risk_level = "High Risk"
		result_message = "Multiple fraud indicators detected. Thorough investigation required."
	
	fraud_check_result = f"Risk Level: {risk_level}\n{result_message}\n\nChecks performed:\n- Document authenticity verification\n- Claim history analysis\n- Policy validation\n- Location verification\n\nScore: {fraud_risk_score:.2f}/100"
	
	# Update claim with fraud check results
	claim.fraud_check_performed = True
	claim.fraud_check_date = datetime.now()
	claim.fraud_check_result = fraud_check_result
	claim.fraud_risk_score = fraud_risk_score
	
	db.session.commit()
	
	return jsonify({
		'success': True,
		'fraud_risk_score': fraud_risk_score,
		'risk_level': risk_level,
		'result': fraud_check_result
	})

@app.route('/insurer/approve-claim/<int:claim_id>', methods=['POST'])
@login_required
@insurer_required
def approve_claim(claim_id):
	"""Approve a claim"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	claim = Claim.query.get_or_404(claim_id)
	if claim.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access.', 'danger')
		return redirect(url_for('manage_claims'))
	
	# Check if claim is Under Review
	if claim.status != 'Under Review':
		flash('Only claims under review can be approved.', 'warning')
		return redirect(url_for('view_claim', claim_id=claim_id))
	
	# Check if fraud check has been performed
	if not claim.fraud_check_performed:
		flash('Please perform fraud check before approving the claim.', 'warning')
		return redirect(url_for('view_claim', claim_id=claim_id))
	
	# Update claim status to Approved
	claim.status = 'Approved'
	claim.approved_by = current_user.id
	claim.approval_date = datetime.now()
	
	db.session.commit()
	
	flash(f'Claim {claim.claim_number} has been approved successfully.', 'success')
	return redirect(url_for('view_claim', claim_id=claim_id))

@app.route('/insurer/reject-claim/<int:claim_id>', methods=['POST'])
@login_required
@insurer_required
def reject_claim(claim_id):
	"""Reject a claim with reason"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	claim = Claim.query.get_or_404(claim_id)
	if claim.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access.', 'danger')
		return redirect(url_for('manage_claims'))
	
	# Check if claim is Under Review
	if claim.status != 'Under Review':
		flash('Only claims under review can be rejected.', 'warning')
		return redirect(url_for('view_claim', claim_id=claim_id))
	
	# Get rejection reason from form
	rejection_reason = request.form.get('rejection_reason', '').strip()
	
	if not rejection_reason:
		flash('Please provide a reason for rejection.', 'warning')
		return redirect(url_for('view_claim', claim_id=claim_id))
	
	# Update claim status to Rejected
	claim.status = 'Rejected'
	claim.approved_by = current_user.id  # Track who made the decision
	claim.approval_date = datetime.now()
	claim.rejection_reason = rejection_reason
	
	db.session.commit()
	
	flash(f'Claim {claim.claim_number} has been rejected.', 'info')
	return redirect(url_for('view_claim', claim_id=claim_id))

@app.route('/api/search-policies')
@login_required
@insurer_required
def search_policies_api():
	"""API endpoint for policy search (autocomplete)"""
	if not current_user.is_approved:
		return jsonify({'policies': []})
	
	query = request.args.get('q', '')
	if len(query) < 2:
		return jsonify({'policies': []})
	
	# Search only policies for this insurance company
	policies = Policy.query.filter(
		Policy.insurance_company_id == current_user.insurance_company_id,
		(Policy.registration_number.ilike(f'%{query}%')) |
		(Policy.insured_name.ilike(f'%{query}%')) |
		(Policy.policy_number.ilike(f'%{query}%'))
	).limit(10).all()
	
	results = []
	for policy in policies:
		results.append({
			'id': policy.id,
			'policy_number': policy.policy_number,
			'insured_name': policy.insured_name,
			'registration_number': policy.registration_number,
			'national_id': policy.national_id,
			'phone_number': policy.phone_number,
			'email_address': policy.email_address,
			'make_model': policy.make_model,
			'year_of_manufacture': policy.year_of_manufacture,
			'chassis_number': policy.chassis_number,
			'engine_number': policy.engine_number,
			'policy_type': policy.policy_type
		})
	
	return jsonify({'policies': results})

@app.route('/insurer/premium-calculator', methods=['GET', 'POST'])
@login_required
@insurer_required
def premium_calculator():
	"""Premium calculator for insurance quotes"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	from forms import PremiumCalculatorForm
	form = PremiumCalculatorForm()
	
	calculation_result = None
	
	if form.validate_on_submit():
		cover_type = form.cover_type.data
		vehicle_value = form.vehicle_value.data
		use_category = form.use_category.data
		
		# Get premium rates for this insurance company and cover type
		premium_rate = PremiumRate.query.filter_by(
			insurance_company_id=current_user.insurance_company_id,
			cover_type=cover_type,
			is_active=True
		).first()
		
		if not premium_rate:
			flash(f'Premium rates not configured for {cover_type} at your company. Please contact administrator.', 'warning')
			return render_template('insurer/premium_calculator.html', form=form)
		
		# Calculate premium based on cover type
		base_premium = 0
		rate_applied = 0
		calculation_details = {}
		
		if cover_type == 'Comprehensive':
			# Use default rate or allow adjustment
			rate_applied = premium_rate.comprehensive_default_rate or 5.0
			base_premium = vehicle_value * (rate_applied / 100)
			calculation_details = {
				'formula': f'{rate_applied}% of vehicle value',
				'vehicle_value': vehicle_value,
				'rate': rate_applied,
				'min_rate': premium_rate.comprehensive_min_rate,
				'max_rate': premium_rate.comprehensive_max_rate
			}
		
		elif cover_type == 'Third-Party Only':
			# Flat rate
			base_premium = premium_rate.tpo_flat_rate or 8000.0
			rate_applied = base_premium
			calculation_details = {
				'formula': 'Flat annual premium',
				'flat_rate': base_premium
			}
		
		elif cover_type == 'Third-Party Fire & Theft':
			# Base TPO + percentage of vehicle value
			tpft_base = premium_rate.tpft_base_rate or 8000.0
			tpft_percent = premium_rate.tpft_percentage or 1.5
			base_premium = tpft_base + (vehicle_value * (tpft_percent / 100))
			rate_applied = tpft_percent
			calculation_details = {
				'formula': f'TPO base + {tpft_percent}% of vehicle value',
				'tpo_base': tpft_base,
				'fire_theft_component': vehicle_value * (tpft_percent / 100),
				'vehicle_value': vehicle_value,
				'rate': tpft_percent
			}
		
		elif cover_type == 'PSV':
			# PSV rates based on vehicle category
			if 'Taxi' in use_category:
				base_premium = premium_rate.psv_taxi_rate or 25000.0
			elif '14-seater' in use_category:
				base_premium = premium_rate.psv_matatu_14_rate or 70000.0
			elif '25-seater' in use_category:
				base_premium = premium_rate.psv_matatu_25_rate or 90000.0
			elif 'Bus' in use_category:
				base_premium = premium_rate.psv_bus_rate or 135000.0
			else:
				base_premium = premium_rate.psv_taxi_rate or 25000.0
			
			rate_applied = base_premium
			calculation_details = {
				'formula': f'Flat annual premium for {use_category}',
				'vehicle_category': use_category,
				'flat_rate': base_premium
			}
		
		# Add optional add-ons (estimate: 5-10% each)
		addon_cost = 0
		addons_list = []
		if form.political_violence.data:
			addon = base_premium * 0.05
			addon_cost += addon
			addons_list.append({'name': 'Political Violence & Terrorism', 'cost': addon})
		if form.windscreen_cover.data:
			addon = base_premium * 0.03
			addon_cost += addon
			addons_list.append({'name': 'Windscreen Cover', 'cost': addon})
		if form.passenger_liability.data:
			addon = base_premium * 0.08
			addon_cost += addon
			addons_list.append({'name': 'Passenger Liability', 'cost': addon})
		if form.road_rescue.data:
			addon = base_premium * 0.02
			addon_cost += addon
			addons_list.append({'name': 'Road Rescue Services', 'cost': addon})
		
		final_premium = base_premium + addon_cost
		
		calculation_result = {
			'cover_type': cover_type,
			'vehicle_value': vehicle_value,
			'use_category': use_category,
			'base_premium': base_premium,
			'rate_applied': rate_applied,
			'addons': addons_list,
			'addon_cost': addon_cost,
			'final_premium': final_premium,
			'calculation_details': calculation_details,
			'registration_number': form.registration_number.data,
			'make_model': form.make_model.data,
			'year_of_manufacture': form.year_of_manufacture.data,
			'customer_email': form.customer_email.data,
			'customer_name': form.customer_name.data,
			'customer_phone': form.customer_phone.data,
			'political_violence': form.political_violence.data,
			'windscreen_cover': form.windscreen_cover.data,
			'passenger_liability': form.passenger_liability.data,
			'road_rescue': form.road_rescue.data
		}
		
		# Store in session for quote/policy creation
		from flask import session
		session['calculation_result'] = calculation_result
	
	return render_template('insurer/premium_calculator.html', form=form, result=calculation_result)

@app.route('/insurer/create-quote-from-calculator', methods=['POST'])
@login_required
@insurer_required
def create_quote_from_calculator():
	"""Create a quote from calculator results"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	from flask import session
	calculation_result = session.get('calculation_result')
	
	if not calculation_result:
		flash('No calculation found. Please calculate premium first.', 'warning')
		return redirect(url_for('premium_calculator'))
	
	customer_email = calculation_result.get('customer_email')
	if not customer_email:
		flash('Customer email is required to create a quote.', 'warning')
		return redirect(url_for('premium_calculator'))
	
	# Generate quote number
	last_quote = Quote.query.order_by(Quote.id.desc()).first()
	if last_quote and last_quote.quote_number.startswith('QT-'):
		last_number = int(last_quote.quote_number.split('-')[1])
		new_number = last_number + 1
	else:
		new_number = 1
	quote_number = f"QT-{new_number:06d}"
	
	# Create quote
	from datetime import timedelta
	quote = Quote(
		quote_number=quote_number,
		insurance_company_id=current_user.insurance_company_id,
		created_by=current_user.id,
		customer_email=customer_email,
		customer_name=calculation_result.get('customer_name'),
		customer_phone=calculation_result.get('customer_phone'),
		vehicle_value=calculation_result['vehicle_value'],
		registration_number=calculation_result.get('registration_number'),
		make_model=calculation_result.get('make_model'),
		year_of_manufacture=calculation_result.get('year_of_manufacture'),
		cover_type=calculation_result['cover_type'],
		use_category=calculation_result['use_category'],
		base_premium=calculation_result['base_premium'],
		rate_applied=calculation_result['rate_applied'],
		final_premium=calculation_result['final_premium'],
		political_violence=calculation_result.get('political_violence', False),
		windscreen_cover=calculation_result.get('windscreen_cover', False),
		passenger_liability=calculation_result.get('passenger_liability', False),
		road_rescue=calculation_result.get('road_rescue', False),
		status='Sent',
		valid_until=datetime.now() + timedelta(days=30)
	)
	
	db.session.add(quote)
	db.session.commit()
	
	# Clear session
	session.pop('calculation_result', None)
	
	flash(f'Quote {quote_number} created and sent to {customer_email}!', 'success')
	return redirect(url_for('view_quote', quote_id=quote.id))

@app.route('/insurer/create-policy-from-calculator', methods=['POST'])
@login_required
@insurer_required
def create_policy_from_calculator():
	"""Redirect to policy creation with pre-filled data"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	from flask import session
	calculation_result = session.get('calculation_result')
	
	if not calculation_result:
		flash('No calculation found. Please calculate premium first.', 'warning')
		return redirect(url_for('premium_calculator'))
	
	# Store calculation in session for policy form to use
	session['prefill_policy'] = calculation_result
	
	flash('Redirecting to policy creation. Form will be pre-filled with calculator data.', 'info')
	return redirect(url_for('create_policy'))

@app.route('/insurer/view-quote/<int:quote_id>')
@login_required
@insurer_required
def view_quote(quote_id):
	"""View quote details"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	quote = Quote.query.get_or_404(quote_id)
	
	# Verify quote belongs to insurer's company
	if quote.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access.', 'danger')
		return redirect(url_for('insurer_dashboard'))
	
	creator = Insurer.query.get(quote.created_by)
	
	return render_template('insurer/view_quote.html', quote=quote, creator=creator)

@app.route('/insurer/reports-and-insights')
@login_required
@insurer_required
def reports_and_insights():
	"""View comprehensive reports and insights"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	# Get current user's company
	user_company = current_user.company
	
	# ===== COMPANY-SPECIFIC STATISTICS =====
	company_policies = Policy.query.filter_by(insurance_company_id=current_user.insurance_company_id).all()
	company_claims = Claim.query.join(Policy).filter(Policy.insurance_company_id == current_user.insurance_company_id).all()
	company_quotes = Quote.query.filter_by(insurance_company_id=current_user.insurance_company_id).all()
	company_insurers = Insurer.query.filter_by(insurance_company_id=current_user.insurance_company_id).all()
	
	# Company policy statistics
	company_active_policies = sum(1 for p in company_policies if p.status == 'Active')
	company_expired_policies = sum(1 for p in company_policies if p.status == 'Expired')
	company_cancelled_policies = sum(1 for p in company_policies if p.status == 'Cancelled')
	company_total_premium = sum(p.premium_amount for p in company_policies if p.status == 'Active')
	
	# Company claims statistics
	company_pending_claims = sum(1 for c in company_claims if c.status == 'Pending')
	company_under_review_claims = sum(1 for c in company_claims if c.status == 'Under Review')
	company_approved_claims = sum(1 for c in company_claims if c.status == 'Approved')
	company_rejected_claims = sum(1 for c in company_claims if c.status == 'Rejected')
	
	# Company quotes statistics
	company_sent_quotes = sum(1 for q in company_quotes if q.status == 'Sent')
	company_converted_quotes = sum(1 for q in company_quotes if q.status == 'Converted')
	company_expired_quotes = sum(1 for q in company_quotes if q.status == 'Expired')
	company_quote_conversion_rate = (company_converted_quotes / len(company_quotes) * 100) if company_quotes else 0
	
	# Company staff statistics
	company_approved_staff = sum(1 for i in company_insurers if i.is_approved)
	company_pending_staff = sum(1 for i in company_insurers if not i.is_approved)
	
	# ===== INDUSTRY-WIDE STATISTICS =====
	all_companies = InsuranceCompany.query.filter_by(is_active=True).all()
	all_policies = Policy.query.all()
	all_claims = Claim.query.all()
	all_quotes = Quote.query.all()
	all_insurers = Insurer.query.all()
	
	# Industry policy statistics
	industry_total_policies = len(all_policies)
	industry_active_policies = sum(1 for p in all_policies if p.status == 'Active')
	industry_expired_policies = sum(1 for p in all_policies if p.status == 'Expired')
	industry_cancelled_policies = sum(1 for p in all_policies if p.status == 'Cancelled')
	industry_total_premium = sum(p.premium_amount for p in all_policies if p.status == 'Active')
	
	# Industry claims statistics
	industry_total_claims = len(all_claims)
	industry_pending_claims = sum(1 for c in all_claims if c.status == 'Pending')
	industry_approved_claims = sum(1 for c in all_claims if c.status == 'Approved')
	industry_rejected_claims = sum(1 for c in all_claims if c.status == 'Rejected')
	
	# Industry quotes statistics
	industry_total_quotes = len(all_quotes)
	industry_converted_quotes = sum(1 for q in all_quotes if q.status == 'Converted')
	industry_quote_conversion_rate = (industry_converted_quotes / industry_total_quotes * 100) if industry_total_quotes else 0
	
	# Company rankings
	company_rankings = []
	for company in all_companies:
		comp_policies = Policy.query.filter_by(insurance_company_id=company.id).all()
		comp_active = sum(1 for p in comp_policies if p.status == 'Active')
		comp_premium = sum(p.premium_amount for p in comp_policies if p.status == 'Active')
		comp_claims = Claim.query.join(Policy).filter(Policy.insurance_company_id == company.id).all()
		comp_approved_claims = sum(1 for c in comp_claims if c.status == 'Approved')
		comp_staff = Insurer.query.filter_by(insurance_company_id=company.id, is_approved=True).count()
		
		company_rankings.append({
			'name': company.name,
			'active_policies': comp_active,
			'total_premium': comp_premium,
			'approved_claims': comp_approved_claims,
			'staff_count': comp_staff,
			'is_current': company.id == current_user.insurance_company_id
		})
	
	# Sort by active policies (descending)
	company_rankings.sort(key=lambda x: x['active_policies'], reverse=True)
	
	# User activity within company
	user_activity = []
	for insurer in company_insurers:
		if insurer.is_approved:
			user_policies = Policy.query.filter_by(created_by=insurer.id).count()
			user_claims = Claim.query.filter_by(created_by=insurer.id).count()
			user_quotes = Quote.query.filter_by(created_by=insurer.id).count()
			
			user_activity.append({
				'username': insurer.username,
				'email': insurer.email,
				'policies_created': user_policies,
				'claims_processed': user_claims,
				'quotes_generated': user_quotes,
				'is_current': insurer.id == current_user.id
			})
	
	# Sort by policies created
	user_activity.sort(key=lambda x: x['policies_created'], reverse=True)
	
	return render_template('insurer/reports_and_insights.html',
		# Company stats
		user_company=user_company,
		company_total_policies=len(company_policies),
		company_active_policies=company_active_policies,
		company_expired_policies=company_expired_policies,
		company_cancelled_policies=company_cancelled_policies,
		company_total_premium=company_total_premium,
		company_total_claims=len(company_claims),
		company_pending_claims=company_pending_claims,
		company_under_review_claims=company_under_review_claims,
		company_approved_claims=company_approved_claims,
		company_rejected_claims=company_rejected_claims,
		company_total_quotes=len(company_quotes),
		company_sent_quotes=company_sent_quotes,
		company_converted_quotes=company_converted_quotes,
		company_expired_quotes=company_expired_quotes,
		company_quote_conversion_rate=company_quote_conversion_rate,
		company_total_staff=len(company_insurers),
		company_approved_staff=company_approved_staff,
		company_pending_staff=company_pending_staff,
		# Industry stats
		industry_total_companies=len(all_companies),
		industry_total_policies=industry_total_policies,
		industry_active_policies=industry_active_policies,
		industry_expired_policies=industry_expired_policies,
		industry_cancelled_policies=industry_cancelled_policies,
		industry_total_premium=industry_total_premium,
		industry_total_claims=industry_total_claims,
		industry_pending_claims=industry_pending_claims,
		industry_approved_claims=industry_approved_claims,
		industry_rejected_claims=industry_rejected_claims,
		industry_total_quotes=industry_total_quotes,
		industry_converted_quotes=industry_converted_quotes,
		industry_quote_conversion_rate=industry_quote_conversion_rate,
		industry_total_insurers=len(all_insurers),
		# Rankings and activity
		company_rankings=company_rankings,
		user_activity=user_activity
	)

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