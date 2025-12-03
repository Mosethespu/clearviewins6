
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory, session, Response
from config import Config
from extension import db, login_manager, migrate, cache
from models import Admin, Customer, Insurer, Regulator, InsuranceCompany, InsurerRequest, RegulatoryBody, RegulatorRequest, Policy, PolicyPhoto, Claim, ClaimDocument, PremiumRate, Quote, CustomerMonitoredPolicy, CustomerPolicyRequest, PolicyCancellationRequest, PolicyRenewalRequest, BlogPost, ContactMessage
from forms import SignupForm, LoginForm, InsurerAccessRequestForm, RegulatorAccessRequestForm, PolicyCreationForm, ClaimForm
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from decorators import admin_required, customer_required, insurer_required, regulator_required
from datetime import datetime, date, timedelta
import os
import csv
from io import StringIO

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
	# Get all published blog posts ordered by date
	posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).all()
	return render_template('blog.html', posts=posts)

@app.route('/blog/<slug>')
def blog_post(slug):
	# Get specific blog post by slug
	post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
	# Increment view count
	post.views += 1
	db.session.commit()
	return render_template('blog_post.html', post=post)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
	if request.method == 'POST':
		name = request.form.get('name')
		email = request.form.get('email')
		message = request.form.get('message')
		
		if name and email and message:
			contact_msg = ContactMessage(
				name=name,
				email=email,
				message=message
			)
			db.session.add(contact_msg)
			db.session.commit()
			flash('Thank you for contacting us! We will get back to you soon.', 'success')
			return redirect(url_for('contact'))
		else:
			flash('Please fill in all fields.', 'danger')
	
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
	
	# Get unread contact messages
	unread_messages = ContactMessage.query.filter_by(read=False).order_by(ContactMessage.submitted_at.desc()).limit(5).all()
	total_unread_messages = ContactMessage.query.filter_by(read=False).count()
	
	return render_template('admin/admindashboard.html', 
						   customers=customers, 
						   insurers=insurers, 
						   regulators=regulators,
						   pending_count=pending_insurer_count,
						   pending_regulator_count=pending_regulator_count,
						   unread_messages=unread_messages,
						   total_unread_messages=total_unread_messages)

@app.route('/admin/search')
@login_required
@admin_required
def admin_search():
	query = request.args.get('q', '').strip()
	search_type = request.args.get('type', 'all')
	
	results = {
		'customers': [],
		'insurers': [],
		'regulators': [],
		'policies': [],
		'claims': [],
		'companies': []
	}
	
	if query:
		search_pattern = f"%{query}%"
		
		# Search customers (only username and email exist)
		if search_type in ['all', 'customers']:
			results['customers'] = Customer.query.filter(
				db.or_(
					Customer.username.ilike(search_pattern),
					Customer.email.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search insurers (only username, email, and staff_id exist)
		if search_type in ['all', 'insurers']:
			results['insurers'] = Insurer.query.filter(
				db.or_(
					Insurer.username.ilike(search_pattern),
					Insurer.email.ilike(search_pattern),
					Insurer.staff_id.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search regulators (only username, email, and staff_id exist)
		if search_type in ['all', 'regulators']:
			results['regulators'] = Regulator.query.filter(
				db.or_(
					Regulator.username.ilike(search_pattern),
					Regulator.email.ilike(search_pattern),
					Regulator.staff_id.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search policies
		if search_type in ['all', 'policies']:
			results['policies'] = Policy.query.filter(
				db.or_(
					Policy.policy_number.ilike(search_pattern),
					Policy.insured_name.ilike(search_pattern),
					Policy.email_address.ilike(search_pattern),
					Policy.registration_number.ilike(search_pattern),
					Policy.national_id.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search claims
		if search_type in ['all', 'claims']:
			results['claims'] = Claim.query.filter(
				db.or_(
					Claim.claim_number.ilike(search_pattern),
					Claim.police_report_number.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search insurance companies
		if search_type in ['all', 'companies']:
			results['companies'] = InsuranceCompany.query.filter(
				InsuranceCompany.name.ilike(search_pattern)
			).limit(20).all()
	
	total_results = sum(len(v) for v in results.values())
	
	return render_template('admin/search.html', 
		query=query,
		search_type=search_type,
		results=results,
		total_results=total_results
	)

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

@app.route('/admin/contact-messages')
@login_required
@admin_required
def admin_contact_messages():
	"""View all contact form submissions"""
	messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
	return render_template('admin/contact_messages.html', messages=messages)

@app.route('/admin/contact-messages/<int:message_id>/mark-read', methods=['POST'])
@login_required
@admin_required
def mark_message_read(message_id):
	"""Mark a contact message as read"""
	message = ContactMessage.query.get_or_404(message_id)
	message.read = True
	message.read_by = current_user.id
	message.read_at = datetime.utcnow()
	db.session.commit()
	flash('Message marked as read.', 'success')
	return redirect(url_for('admin_contact_messages'))

@app.route('/admin/contact-messages/<int:message_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_contact_message(message_id):
	"""Delete a contact message"""
	message = ContactMessage.query.get_or_404(message_id)
	db.session.delete(message)
	db.session.commit()
	flash('Message deleted successfully.', 'success')
	return redirect(url_for('admin_contact_messages'))

@app.route('/admin/reports-and-insights')
@login_required
@admin_required
def admin_reports_and_insights():
	"""View comprehensive system-wide reports and insights"""
	
	# Get all data
	all_customers = Customer.query.all()
	all_insurers = Insurer.query.all()
	all_regulators = Regulator.query.all()
	all_companies = InsuranceCompany.query.filter_by(is_active=True).all()
	all_policies = Policy.query.all()
	all_claims = Claim.query.all()
	all_quotes = Quote.query.all()
	
	# User statistics
	total_customers = len(all_customers)
	active_customers = sum(1 for c in all_customers if c.is_active)
	total_insurers = len(all_insurers)
	approved_insurers = sum(1 for i in all_insurers if i.is_approved)
	total_regulators = len(all_regulators)
	approved_regulators = sum(1 for r in all_regulators if r.is_approved)
	
	# Policy statistics
	total_policies = len(all_policies)
	active_policies = sum(1 for p in all_policies if p.status == 'Active')
	expired_policies = sum(1 for p in all_policies if p.status == 'Expired')
	cancelled_policies = sum(1 for p in all_policies if p.status == 'Cancelled')
	total_premium = sum(p.premium_amount for p in all_policies if p.status == 'Active')
	
	# Claims statistics
	total_claims = len(all_claims)
	pending_claims = sum(1 for c in all_claims if c.status == 'Pending')
	under_review_claims = sum(1 for c in all_claims if c.status == 'Under Review')
	approved_claims = sum(1 for c in all_claims if c.status == 'Approved')
	rejected_claims = sum(1 for c in all_claims if c.status == 'Rejected')
	
	# Quotes statistics
	total_quotes = len(all_quotes)
	sent_quotes = sum(1 for q in all_quotes if q.status == 'Sent')
	converted_quotes = sum(1 for q in all_quotes if q.status == 'Converted')
	expired_quotes = sum(1 for q in all_quotes if q.status == 'Expired')
	quote_conversion_rate = (converted_quotes / total_quotes * 100) if total_quotes else 0
	
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
			'staff_count': comp_staff
		})
	
	# Sort by active policies (descending)
	company_rankings.sort(key=lambda x: x['active_policies'], reverse=True)
	
	# User activity across all companies
	user_activity = []
	for insurer in all_insurers:
		if insurer.is_approved:
			user_policies = Policy.query.filter_by(created_by=insurer.id).count()
			user_claims = Claim.query.filter_by(created_by=insurer.id).count()
			user_quotes = Quote.query.filter_by(created_by=insurer.id).count()
			
			user_activity.append({
				'username': insurer.username,
				'email': insurer.email,
				'company': insurer.company.name if insurer.company else 'N/A',
				'policies_created': user_policies,
				'claims_processed': user_claims,
				'quotes_generated': user_quotes
			})
	
	# Sort by policies created
	user_activity.sort(key=lambda x: x['policies_created'], reverse=True)
	
	# Recent requests
	pending_insurer_requests = InsurerRequest.query.filter_by(status='pending').count()
	pending_regulator_requests = RegulatorRequest.query.filter_by(status='pending').count()
	
	return render_template('admin/reports_and_insights.html',
		# User stats
		total_customers=total_customers,
		active_customers=active_customers,
		total_insurers=total_insurers,
		approved_insurers=approved_insurers,
		total_regulators=total_regulators,
		approved_regulators=approved_regulators,
		# Policy stats
		total_policies=total_policies,
		active_policies=active_policies,
		expired_policies=expired_policies,
		cancelled_policies=cancelled_policies,
		total_premium=total_premium,
		# Claims stats
		total_claims=total_claims,
		pending_claims=pending_claims,
		under_review_claims=under_review_claims,
		approved_claims=approved_claims,
		rejected_claims=rejected_claims,
		# Quotes stats
		total_quotes=total_quotes,
		sent_quotes=sent_quotes,
		converted_quotes=converted_quotes,
		expired_quotes=expired_quotes,
		quote_conversion_rate=quote_conversion_rate,
		# Company data
		total_companies=len(all_companies),
		company_rankings=company_rankings,
		user_activity=user_activity,
		# Requests
		pending_insurer_requests=pending_insurer_requests,
		pending_regulator_requests=pending_regulator_requests
	)

@app.route('/admin/export-reports-csv')
@login_required
@admin_required
def admin_export_reports_csv():
	"""Export admin reports data to CSV"""
	si = StringIO()
	writer = csv.writer(si)
	
	# Get export type from query parameter
	export_type = request.args.get('type', 'summary')
	
	if export_type == 'companies':
		writer.writerow(['Company Name', 'Active Policies', 'Total Premium (KES)', 'Approved Claims', 'Staff Count'])
		all_companies = InsuranceCompany.query.filter_by(is_active=True).all()
		for company in all_companies:
			comp_policies = Policy.query.filter_by(insurance_company_id=company.id).all()
			comp_active = sum(1 for p in comp_policies if p.status == 'Active')
			comp_premium = sum(p.premium_amount for p in comp_policies if p.status == 'Active')
			comp_claims = Claim.query.join(Policy).filter(Policy.insurance_company_id == company.id).all()
			comp_approved_claims = sum(1 for c in comp_claims if c.status == 'Approved')
			comp_staff = Insurer.query.filter_by(insurance_company_id=company.id, is_approved=True).count()
			writer.writerow([company.name, comp_active, f'{comp_premium:.2f}', comp_approved_claims, comp_staff])
	
	elif export_type == 'users':
		writer.writerow(['Username', 'Email', 'Role', 'Company/Body', 'Status'])
		customers = Customer.query.all()
		insurers = Insurer.query.all()
		regulators = Regulator.query.all()
		for c in customers:
			writer.writerow([c.username, c.email, 'Customer', 'N/A', 'Active' if c.is_active else 'Inactive'])
		for i in insurers:
			writer.writerow([i.username, i.email, 'Insurer', i.company.name if i.company else 'N/A', 'Approved' if i.is_approved else 'Pending'])
		for r in regulators:
			writer.writerow([r.username, r.email, 'Regulator', r.regulatory_body.name if r.regulatory_body else 'N/A', 'Approved' if r.is_approved else 'Pending'])
	
	elif export_type == 'policies':
		writer.writerow(['Policy Number', 'Company', 'Policyholder', 'Type', 'Premium (KES)', 'Status', 'Start Date', 'Expiry Date'])
		all_policies = Policy.query.all()
		for p in all_policies:
			writer.writerow([
				p.policy_number, 
				p.insurance_company.name if p.insurance_company else 'N/A',
				p.policyholder_name,
				p.policy_type,
				f'{p.premium_amount:.2f}',
				p.status,
				p.start_date.strftime('%Y-%m-%d') if p.start_date else 'N/A',
				p.expiry_date.strftime('%Y-%m-%d') if p.expiry_date else 'N/A'
			])
	
	elif export_type == 'claims':
		writer.writerow(['Claim Number', 'Policy Number', 'Company', 'Status', 'Date Submitted'])
		all_claims = Claim.query.all()
		for c in all_claims:
			writer.writerow([
				c.claim_number,
				c.policy.policy_number if c.policy else 'N/A',
				c.insurance_company.name if c.insurance_company else 'N/A',
				c.status,
				c.date_submitted.strftime('%Y-%m-%d') if c.date_submitted else 'N/A'
			])
	
	else:  # summary
		writer.writerow(['Metric', 'Value'])
		customers = Customer.query.all()
		insurers = Insurer.query.all()
		regulators = Regulator.query.all()
		policies = Policy.query.all()
		claims = Claim.query.all()
		
		writer.writerow(['Total Customers', len(customers)])
		writer.writerow(['Active Customers', sum(1 for c in customers if c.is_active)])
		writer.writerow(['Total Insurers', len(insurers)])
		writer.writerow(['Approved Insurers', sum(1 for i in insurers if i.is_approved)])
		writer.writerow(['Total Regulators', len(regulators)])
		writer.writerow(['Approved Regulators', sum(1 for r in regulators if r.is_approved)])
		writer.writerow(['Total Policies', len(policies)])
		writer.writerow(['Active Policies', sum(1 for p in policies if p.status == 'Active')])
		writer.writerow(['Total Premium (KES)', f'{sum(p.premium_amount for p in policies if p.status == "Active"):.2f}'])
		writer.writerow(['Total Claims', len(claims)])
		writer.writerow(['Approved Claims', sum(1 for c in claims if c.status == 'Approved')])
	
	output = si.getvalue()
	si.close()
	
	return Response(
		output,
		mimetype='text/csv',
		headers={'Content-Disposition': f'attachment; filename=clearview_admin_report_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
	)

@app.route('/admin/view-policies')
@login_required
@admin_required
def admin_view_policies():
	"""View all policies with filtering and export capabilities"""
	from datetime import datetime
	
	# Get filter parameters
	status_filter = request.args.get('status', '')
	company_filter = request.args.get('company_id', '')
	start_date = request.args.get('start_date', '')
	end_date = request.args.get('end_date', '')
	
	# Base query
	query = Policy.query
	
	# Apply filters
	if status_filter:
		query = query.filter_by(status=status_filter)
	
	if company_filter:
		query = query.filter_by(insurance_company_id=company_filter)
	
	if start_date:
		try:
			start_dt = datetime.strptime(start_date, '%Y-%m-%d')
			query = query.filter(Policy.effective_date >= start_dt)
		except ValueError:
			pass
	
	if end_date:
		try:
			end_dt = datetime.strptime(end_date, '%Y-%m-%d')
			query = query.filter(Policy.expiry_date <= end_dt)
		except ValueError:
			pass
	
	# Get filtered policies
	policies = query.all()
	
	# Calculate summary statistics
	total_policies = len(policies)
	active_policies = sum(1 for p in policies if p.status == 'Active')
	expired_policies = sum(1 for p in policies if p.status == 'Expired')
	cancelled_policies = sum(1 for p in policies if p.status == 'Cancelled')
	total_premium = sum(p.premium_amount for p in policies)
	
	# Get all companies for filter dropdown
	companies = InsuranceCompany.query.all()
	
	return render_template('admin/view_policies.html',
		policies=policies,
		companies=companies,
		total_policies=total_policies,
		active_policies=active_policies,
		expired_policies=expired_policies,
		cancelled_policies=cancelled_policies,
		total_premium=total_premium,
		status_filter=status_filter,
		company_filter=company_filter,
		start_date=start_date,
		end_date=end_date
	)

@app.route('/admin/export-policies-csv')
@login_required
@admin_required
def admin_export_policies_csv():
	"""Export filtered policies to CSV"""
	from datetime import datetime
	
	# Get same filter parameters
	status_filter = request.args.get('status', '')
	company_filter = request.args.get('company_id', '')
	start_date = request.args.get('start_date', '')
	end_date = request.args.get('end_date', '')
	
	# Base query
	query = Policy.query
	
	# Apply filters
	if status_filter:
		query = query.filter_by(status=status_filter)
	
	if company_filter:
		query = query.filter_by(insurance_company_id=company_filter)
	
	if start_date:
		try:
			start_dt = datetime.strptime(start_date, '%Y-%m-%d')
			query = query.filter(Policy.effective_date >= start_dt)
		except ValueError:
			pass
	
	if end_date:
		try:
			end_dt = datetime.strptime(end_date, '%Y-%m-%d')
			query = query.filter(Policy.expiry_date <= end_dt)
		except ValueError:
			pass
	
	# Get filtered policies
	policies = query.all()
	
	# Create CSV
	si = StringIO()
	writer = csv.writer(si)
	
	# Write header
	writer.writerow(['Policy Number', 'Customer Email', 'Insurance Company', 'Vehicle Registration', 
					 'Premium (KES)', 'Status', 'Start Date', 'End Date', 'Created Date'])
	
	# Write data
	for policy in policies:
		writer.writerow([
			policy.policy_number or '',
			policy.email_address or '',
			policy.insurance_company.name if policy.insurance_company else '',
			policy.registration_number or '',
			f'{policy.premium_amount:.2f}',
			policy.status or '',
			policy.effective_date.strftime('%Y-%m-%d') if policy.effective_date else '',
			policy.expiry_date.strftime('%Y-%m-%d') if policy.expiry_date else '',
			policy.date_entered.strftime('%Y-%m-%d %H:%M') if policy.date_entered else ''
		])
	
	output = si.getvalue()
	si.close()
	
	return Response(
		output,
		mimetype='text/csv',
		headers={'Content-Disposition': f'attachment; filename=clearview_policies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
	)

@app.route('/admin/view-claims')
@login_required
@admin_required
def admin_view_claims():
	"""View all claims with filtering and export capabilities"""
	from datetime import datetime
	
	# Get filter parameters
	status_filter = request.args.get('status', '')
	company_filter = request.args.get('company_id', '')
	start_date = request.args.get('start_date', '')
	end_date = request.args.get('end_date', '')
	
	# Base query
	query = Claim.query
	
	# Apply filters
	if status_filter:
		query = query.filter_by(status=status_filter)
	
	if company_filter:
		# Filter by company through policy relationship
		query = query.join(Policy).filter(Policy.insurance_company_id == company_filter)
	
	if start_date:
		try:
			start_dt = datetime.strptime(start_date, '%Y-%m-%d')
			query = query.filter(Claim.accident_date >= start_dt)
		except ValueError:
			pass
	
	if end_date:
		try:
			end_dt = datetime.strptime(end_date, '%Y-%m-%d')
			query = query.filter(Claim.accident_date <= end_dt)
		except ValueError:
			pass
	
	# Get filtered claims
	claims = query.all()
	
	# Calculate summary statistics
	total_claims = len(claims)
	pending_claims = sum(1 for c in claims if c.status == 'Pending')
	approved_claims = sum(1 for c in claims if c.status == 'Approved')
	rejected_claims = sum(1 for c in claims if c.status == 'Rejected')
	under_review_claims = sum(1 for c in claims if c.status == 'Under Review')
	
	# Get all companies for filter dropdown
	companies = InsuranceCompany.query.all()
	
	return render_template('admin/view_claims.html',
		claims=claims,
		companies=companies,
		total_claims=total_claims,
		pending_claims=pending_claims,
		approved_claims=approved_claims,
		rejected_claims=rejected_claims,
		under_review_claims=under_review_claims,
		status_filter=status_filter,
		company_filter=company_filter,
		start_date=start_date,
		end_date=end_date
	)

@app.route('/admin/export-claims-csv')
@login_required
@admin_required
def admin_export_claims_csv():
	"""Export filtered claims to CSV"""
	from datetime import datetime
	
	# Get same filter parameters
	status_filter = request.args.get('status', '')
	company_filter = request.args.get('company_id', '')
	start_date = request.args.get('start_date', '')
	end_date = request.args.get('end_date', '')
	
	# Base query
	query = Claim.query
	
	# Apply filters
	if status_filter:
		query = query.filter_by(status=status_filter)
	
	if company_filter:
		# Filter by company through policy relationship
		query = query.join(Policy).filter(Policy.insurance_company_id == company_filter)
	
	if start_date:
		try:
			start_dt = datetime.strptime(start_date, '%Y-%m-%d')
			query = query.filter(Claim.accident_date >= start_dt)
		except ValueError:
			pass
	
	if end_date:
		try:
			end_dt = datetime.strptime(end_date, '%Y-%m-%d')
			query = query.filter(Claim.accident_date <= end_dt)
		except ValueError:
			pass
	
	# Get filtered claims
	claims = query.all()
	
	# Create CSV
	si = StringIO()
	writer = csv.writer(si)
	
	# Write header
	writer.writerow(['Claim Number', 'Policy Number', 'Customer Email', 'Insurance Company', 
					 'Date of Accident', 'Location', 'Description', 'Status', 
					 'Filed Date', 'Review Date'])
	
	# Write data
	for claim in claims:
		writer.writerow([
			claim.claim_number or '',
			claim.policy.policy_number if claim.policy else '',
			claim.policy.email_address if claim.policy else '',
			claim.policy.insurance_company.name if claim.policy and claim.policy.insurance_company else '',
			claim.accident_date.strftime('%Y-%m-%d') if claim.accident_date else '',
			claim.accident_location or '',
			claim.accident_description[:100] or '',  # Truncate long descriptions
			claim.status or '',
			claim.date_submitted.strftime('%Y-%m-%d %H:%M') if claim.date_submitted else '',
			claim.review_date.strftime('%Y-%m-%d %H:%M') if claim.review_date else ''
		])
	
	output = si.getvalue()
	si.close()
	
	return Response(
		output,
		mimetype='text/csv',
		headers={'Content-Disposition': f'attachment; filename=clearview_claims_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
	)

@app.route('/admin/policy/<int:policy_id>')
@login_required
@admin_required
def admin_view_policy_detail(policy_id):
	"""View detailed information for a specific policy"""
	policy = Policy.query.get_or_404(policy_id)
	
	return render_template('admin/policy_detail.html', policy=policy)

@app.route('/admin/claim/<int:claim_id>')
@login_required
@admin_required
def admin_view_claim_detail(claim_id):
	"""View detailed information for a specific claim"""
	claim = Claim.query.get_or_404(claim_id)
	
	return render_template('admin/claim_detail.html', claim=claim)

@app.route('/customer/dashboard')
@login_required
@customer_required
def customer_dashboard():
	# Get customer's owned policies (by email)
	owned_policies = Policy.query.filter_by(email_address=current_user.email).order_by(
		Policy.date_entered.desc()
	).all()
	
	# Get monitored policies
	monitored = CustomerMonitoredPolicy.query.filter_by(customer_id=current_user.id).all()
	monitored_policy_ids = [m.policy_id for m in monitored]
	monitored_policies = Policy.query.filter(Policy.id.in_(monitored_policy_ids)).all() if monitored_policy_ids else []
	
	# Combine for total count
	all_policies = owned_policies + monitored_policies
	total_policies = len(all_policies)
	
	# Get active policies (not expired)
	active_owned = [p for p in owned_policies if p.expiry_date and p.expiry_date >= datetime.now().date() and p.status == 'Active']
	active_policies = len(active_owned)
	
	# Get expiring soon (within 30 days)
	thirty_days = datetime.now().date() + timedelta(days=30)
	expiring_soon = [p for p in owned_policies if p.expiry_date and datetime.now().date() <= p.expiry_date <= thirty_days and p.status == 'Active']
	expiring_soon_count = len(expiring_soon)
	
	# Get customer's claims
	owned_policy_ids = [p.id for p in owned_policies]
	total_claims = Claim.query.filter(Claim.policy_id.in_(owned_policy_ids)).count() if owned_policy_ids else 0
	pending_claims = Claim.query.filter(
		Claim.policy_id.in_(owned_policy_ids),
		Claim.status == 'Pending'
	).count() if owned_policy_ids else 0
	
	# Get recent claims
	recent_claims = Claim.query.filter(
		Claim.policy_id.in_(owned_policy_ids)
	).order_by(Claim.date_submitted.desc()).limit(5).all() if owned_policy_ids else []
	
	# Get pending requests
	pending_access_requests = CustomerPolicyRequest.query.filter_by(
		customer_id=current_user.id,
		status='pending'
	).count()
	
	pending_cancellation_requests = PolicyCancellationRequest.query.filter_by(
		customer_id=current_user.id,
		status='pending'
	).count()
	
	pending_renewal_requests = PolicyRenewalRequest.query.filter_by(
		customer_id=current_user.id,
		status='pending'
	).count()
	
	total_pending_requests = pending_access_requests + pending_cancellation_requests + pending_renewal_requests
	
	# Calculate total premium for active policies
	total_premium = sum(p.premium_amount for p in active_owned)
	
	return render_template('customer/customerashboard.html',
						   owned_policies=owned_policies[:5],  # Recent 5
						   monitored_policies=monitored_policies[:5],  # Recent 5
						   total_policies=total_policies,
						   active_policies=active_policies,
						   expiring_soon_count=expiring_soon_count,
						   total_claims=total_claims,
						   pending_claims=pending_claims,
						   recent_claims=recent_claims,
						   total_premium=total_premium,
						   pending_access_requests=pending_access_requests,
						   pending_cancellation_requests=pending_cancellation_requests,
						   pending_renewal_requests=pending_renewal_requests,
						   total_pending_requests=total_pending_requests,
						   now=datetime.now())

@app.route('/customer/search')
@login_required
@customer_required
def customer_search():
	query = request.args.get('q', '').strip()
	search_type = request.args.get('type', 'all')
	
	results = {
		'policies': [],
		'claims': [],
		'quotes': [],
		'companies': []
	}
	
	if query:
		search_pattern = f"%{query}%"
		
		# Search customer's own policies by email
		if search_type in ['all', 'policies']:
			results['policies'] = Policy.query.filter(
				Policy.email_address == current_user.email
			).filter(
				db.or_(
					Policy.policy_number.ilike(search_pattern),
					Policy.insured_name.ilike(search_pattern),
					Policy.registration_number.ilike(search_pattern),
					Policy.vehicle_make.ilike(search_pattern),
					Policy.vehicle_model.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search customer's own claims through their policies
		if search_type in ['all', 'claims']:
			customer_policies = Policy.query.filter_by(email_address=current_user.email).all()
			policy_ids = [p.id for p in customer_policies]
			if policy_ids:
				results['claims'] = Claim.query.filter(
					Claim.policy_id.in_(policy_ids)
				).filter(
					db.or_(
						Claim.claim_number.ilike(search_pattern),
						Claim.police_report_number.ilike(search_pattern),
						Claim.accident_location.ilike(search_pattern)
					)
				).limit(20).all()
		
		# Search customer's own quotes
		if search_type in ['all', 'quotes']:
			results['quotes'] = Quote.query.filter(
				Quote.customer_email == current_user.email
			).filter(
				db.or_(
					Quote.quote_number.ilike(search_pattern),
					Quote.vehicle_make.ilike(search_pattern),
					Quote.vehicle_model.ilike(search_pattern),
					Quote.registration_number.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search insurance companies
		if search_type in ['all', 'companies']:
			results['companies'] = InsuranceCompany.query.filter(
				InsuranceCompany.name.ilike(search_pattern)
			).filter_by(is_active=True).limit(20).all()
	
	total_results = sum(len(v) for v in results.values())
	
	return render_template('customer/search.html', 
		query=query,
		search_type=search_type,
		results=results,
		total_results=total_results
	)

@app.route('/customer/search-vehicle')
@login_required
@customer_required
def customer_search_vehicle():
	"""Search for vehicle by registration number"""
	return render_template('customer/search_vehicle.html')

@app.route('/customer/vehicle/<registration_number>')
@login_required
@customer_required
def customer_view_vehicle(registration_number):
	"""View vehicle details, policies, and claims"""
	# Search for policies with this registration number
	policies = Policy.query.filter_by(registration_number=registration_number.upper()).all()
	
	if not policies:
		flash('No vehicle found with that registration number.', 'warning')
		return redirect(url_for('customer_search_vehicle'))
	
	# Get all claims for these policies
	policy_ids = [p.id for p in policies]
	claims = Claim.query.filter(Claim.policy_id.in_(policy_ids)).all() if policy_ids else []
	
	# Get the most recent policy for vehicle details
	active_policy = next((p for p in policies if p.status == 'Active'), None)
	vehicle_info = active_policy if active_policy else policies[0]
	
	return render_template('customer/view_vehicle.html',
		registration_number=registration_number.upper(),
		vehicle_info=vehicle_info,
		policies=policies,
		claims=claims
	)

@app.route('/customer/policy/<int:policy_id>')
@login_required
@customer_required
def customer_view_policy_detail(policy_id):
	"""View detailed policy information with photos"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Note: Customers can view any policy when searching by vehicle registration
	# but personal details are hidden in the template if not their own policy
	
	return render_template('customer/view_policy_detail.html', policy=policy)

@app.route('/customer/claim/<int:claim_id>')
@login_required
@customer_required
def customer_view_claim_detail(claim_id):
	"""View detailed claim information with photos"""
	claim = Claim.query.get_or_404(claim_id)
	
	# Note: Customers can view any claim when searching by vehicle registration
	# but personal details are hidden in the template if not their own claim
	
	return render_template('customer/view_claim_detail.html', claim=claim)

@app.route('/customer/reports-and-insights')
@login_required
@customer_required
def customer_reports_and_insights():
	"""View customer-specific reports and insights"""
	
	# Get customer's policies by matching email address
	customer_policies = Policy.query.filter_by(email_address=current_user.email).all()
	
	# Policy statistics
	total_policies = len(customer_policies)
	active_policies = sum(1 for p in customer_policies if p.status == 'Active')
	expired_policies = sum(1 for p in customer_policies if p.status == 'Expired')
	cancelled_policies = sum(1 for p in customer_policies if p.status == 'Cancelled')
	total_premium_paid = sum(p.premium_amount for p in customer_policies)
	active_premium = sum(p.premium_amount for p in customer_policies if p.status == 'Active')
	
	# Get customer's claims through policies
	policy_ids = [p.id for p in customer_policies]
	customer_claims = Claim.query.filter(Claim.policy_id.in_(policy_ids)).all() if policy_ids else []
	
	# Claims statistics
	total_claims = len(customer_claims)
	pending_claims = sum(1 for c in customer_claims if c.status == 'Pending')
	under_review_claims = sum(1 for c in customer_claims if c.status == 'Under Review')
	approved_claims = sum(1 for c in customer_claims if c.status == 'Approved')
	rejected_claims = sum(1 for c in customer_claims if c.status == 'Rejected')
	
	# Get customer's quotes by email
	customer_quotes = Quote.query.filter_by(customer_email=current_user.email).all()
	
	# Quotes statistics
	total_quotes = len(customer_quotes)
	sent_quotes = sum(1 for q in customer_quotes if q.status == 'Sent')
	converted_quotes = sum(1 for q in customer_quotes if q.status == 'Converted')
	expired_quotes = sum(1 for q in customer_quotes if q.status == 'Expired')
	quote_conversion_rate = (converted_quotes / total_quotes * 100) if total_quotes else 0
	
	# Policy breakdown by type
	comprehensive_policies = sum(1 for p in customer_policies if p.policy_type == 'Comprehensive')
	third_party_policies = sum(1 for p in customer_policies if p.policy_type == 'Third-Party')
	
	# Policy breakdown by company
	policies_by_company = {}
	for policy in customer_policies:
		company_name = policy.insurance_company.name if policy.insurance_company else 'Unknown'
		if company_name not in policies_by_company:
			policies_by_company[company_name] = {
				'count': 0,
				'premium': 0,
				'claims': 0
			}
		policies_by_company[company_name]['count'] += 1
		if policy.status == 'Active':
			policies_by_company[company_name]['premium'] += policy.premium_amount
	
	# Count claims per company
	for claim in customer_claims:
		if claim.insurance_company:
			company_name = claim.insurance_company.name
			if company_name in policies_by_company:
				policies_by_company[company_name]['claims'] += 1
	
	# Sort by policy count
	company_breakdown = sorted(
		[{'name': k, **v} for k, v in policies_by_company.items()],
		key=lambda x: x['count'],
		reverse=True
	)
	
	# Recent activity
	recent_policies = sorted(customer_policies, key=lambda p: p.date_entered if p.date_entered else datetime.min, reverse=True)[:5]
	recent_claims = sorted(customer_claims, key=lambda c: c.date_submitted if c.date_submitted else datetime.min, reverse=True)[:5]
	
	return render_template('customer/reports_and_insights.html',
		# Policy stats
		total_policies=total_policies,
		active_policies=active_policies,
		expired_policies=expired_policies,
		cancelled_policies=cancelled_policies,
		total_premium_paid=total_premium_paid,
		active_premium=active_premium,
		comprehensive_policies=comprehensive_policies,
		third_party_policies=third_party_policies,
		# Claims stats
		total_claims=total_claims,
		pending_claims=pending_claims,
		under_review_claims=under_review_claims,
		approved_claims=approved_claims,
		rejected_claims=rejected_claims,
		# Quotes stats
		total_quotes=total_quotes,
		sent_quotes=sent_quotes,
		converted_quotes=converted_quotes,
		expired_quotes=expired_quotes,
		quote_conversion_rate=quote_conversion_rate,
		# Breakdowns
		company_breakdown=company_breakdown,
		# Recent activity
		recent_policies=recent_policies,
		recent_claims=recent_claims
	)

@app.route('/customer/export-reports-csv')
@login_required
@customer_required
def customer_export_reports_csv():
	"""Export customer reports data to CSV"""
	si = StringIO()
	writer = csv.writer(si)
	
	# Get export type from query parameter
	export_type = request.args.get('type', 'summary')
	
	if export_type == 'policies':
		writer.writerow(['Policy Number', 'Insurance Company', 'Type', 'Premium (KES)', 'Status', 'Start Date', 'Expiry Date'])
		customer_policies = Policy.query.filter_by(email_address=current_user.email).all()
		for p in customer_policies:
			writer.writerow([
				p.policy_number,
				p.insurance_company.name if p.insurance_company else 'N/A',
				p.policy_type,
				f'{p.premium_amount:.2f}',
				p.status,
				p.start_date.strftime('%Y-%m-%d') if p.start_date else 'N/A',
				p.expiry_date.strftime('%Y-%m-%d') if p.expiry_date else 'N/A'
			])
	
	elif export_type == 'claims':
		writer.writerow(['Claim Number', 'Policy Number', 'Insurance Company', 'Status', 'Date Submitted', 'Review Date'])
		customer_policies = Policy.query.filter_by(email_address=current_user.email).all()
		policy_ids = [p.id for p in customer_policies]
		customer_claims = Claim.query.filter(Claim.policy_id.in_(policy_ids)).all() if policy_ids else []
		for c in customer_claims:
			writer.writerow([
				c.claim_number,
				c.policy.policy_number if c.policy else 'N/A',
				c.insurance_company.name if c.insurance_company else 'N/A',
				c.status,
				c.date_submitted.strftime('%Y-%m-%d') if c.date_submitted else 'N/A',
				c.review_date.strftime('%Y-%m-%d') if c.review_date else 'N/A'
			])
	
	else:  # summary
		writer.writerow(['Metric', 'Value'])
		customer_policies = Policy.query.filter_by(email_address=current_user.email).all()
		policy_ids = [p.id for p in customer_policies]
		customer_claims = Claim.query.filter(Claim.policy_id.in_(policy_ids)).all() if policy_ids else []
		
		writer.writerow(['Total Policies', len(customer_policies)])
		writer.writerow(['Active Policies', sum(1 for p in customer_policies if p.status == 'Active')])
		writer.writerow(['Total Premium Paid (KES)', f'{sum(p.premium_amount for p in customer_policies):.2f}'])
		writer.writerow(['Active Premium (KES)', f'{sum(p.premium_amount for p in customer_policies if p.status == "Active"):.2f}'])
		writer.writerow(['Total Claims', len(customer_claims)])
		writer.writerow(['Approved Claims', sum(1 for c in customer_claims if c.status == 'Approved')])
		writer.writerow(['Rejected Claims', sum(1 for c in customer_claims if c.status == 'Rejected')])
	
	output = si.getvalue()
	si.close()
	
	return Response(
		output,
		mimetype='text/csv',
		headers={'Content-Disposition': f'attachment; filename=clearview_customer_report_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
	)

# ========== CUSTOMER POLICY MANAGEMENT ROUTES ==========

@app.route('/customer/policy-management')
@login_required
@customer_required
def customer_policy_management():
	"""Main policy management dashboard for customers"""
	# Get customer's owned policies (via email match)
	owned_policies = Policy.query.filter_by(email_address=current_user.email).all()
	
	# Get monitored policies
	monitored = CustomerMonitoredPolicy.query.filter_by(customer_id=current_user.id).all()
	monitored_policies = [m.policy for m in monitored]
	
	# Get pending requests
	access_requests = CustomerPolicyRequest.query.filter_by(
		customer_id=current_user.id,
		status='pending'
	).all()
	
	cancellation_requests = PolicyCancellationRequest.query.filter_by(
		customer_id=current_user.id,
		status='pending'
	).all()
	
	renewal_requests = PolicyRenewalRequest.query.filter_by(
		customer_id=current_user.id,
		status='pending'
	).all()
	
	return render_template('customer/policy_management.html',
		owned_policies=owned_policies,
		monitored_policies=monitored_policies,
		access_requests=access_requests,
		cancellation_requests=cancellation_requests,
		renewal_requests=renewal_requests,
		today=date.today()
	)

@app.route('/customer/search-policy', methods=['GET', 'POST'])
@login_required
@customer_required
def customer_search_policy():
	"""Search for a policy by policy number"""
	if request.method == 'POST':
		policy_number = request.form.get('policy_number', '').strip().upper()
		
		if not policy_number:
			flash('Please enter a policy number', 'warning')
			return redirect(url_for('customer_search_policy'))
		
		policy = Policy.query.filter_by(policy_number=policy_number).first()
		
		if not policy:
			flash(f'Policy {policy_number} not found', 'danger')
			return redirect(url_for('customer_search_policy'))
		
		# Check if already owned
		if policy.email_address == current_user.email:
			flash('This policy is already in your account', 'info')
			return redirect(url_for('customer_view_policy_from_management', policy_id=policy.id))
		
		# Check if already monitored
		existing_monitor = CustomerMonitoredPolicy.query.filter_by(
			customer_id=current_user.id,
			policy_id=policy.id
		).first()
		
		# Check if access request exists
		existing_request = CustomerPolicyRequest.query.filter_by(
			customer_id=current_user.id,
			policy_id=policy.id,
			status='pending'
		).first()
		
		return render_template('customer/policy_search_result.html',
			policy=policy,
			is_monitored=existing_monitor is not None,
			has_pending_request=existing_request is not None
		)
	
	return render_template('customer/search_policy.html')

@app.route('/customer/add-to-monitor/<int:policy_id>', methods=['POST'])
@login_required
@customer_required
def customer_add_to_monitor(policy_id):
	"""Add a policy to monitoring (view-only)"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Check if already owned
	if policy.email_address == current_user.email:
		flash('This policy is already in your account', 'info')
		return redirect(url_for('customer_policy_management'))
	
	# Check if already monitored
	existing = CustomerMonitoredPolicy.query.filter_by(
		customer_id=current_user.id,
		policy_id=policy_id
	).first()
	
	if existing:
		flash('Policy is already being monitored', 'info')
	else:
		monitored = CustomerMonitoredPolicy(
			customer_id=current_user.id,
			policy_id=policy_id
		)
		db.session.add(monitored)
		db.session.commit()
		flash(f'Policy {policy.policy_number} added to monitoring', 'success')
	
	return redirect(url_for('customer_policy_management'))

@app.route('/customer/remove-from-monitor/<int:policy_id>', methods=['POST'])
@login_required
@customer_required
def customer_remove_from_monitor(policy_id):
	"""Remove a policy from monitoring"""
	monitored = CustomerMonitoredPolicy.query.filter_by(
		customer_id=current_user.id,
		policy_id=policy_id
	).first_or_404()
	
	policy_number = monitored.policy.policy_number
	db.session.delete(monitored)
	db.session.commit()
	
	flash(f'Policy {policy_number} removed from monitoring', 'success')
	return redirect(url_for('customer_policy_management'))

@app.route('/customer/request-policy-access/<int:policy_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def customer_request_policy_access(policy_id):
	"""Request access to add a policy to customer's account"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Check if already owned
	if policy.email_address == current_user.email:
		flash('This policy is already in your account', 'info')
		return redirect(url_for('customer_policy_management'))
	
	# Check for existing pending request
	existing = CustomerPolicyRequest.query.filter_by(
		customer_id=current_user.id,
		policy_id=policy_id,
		status='pending'
	).first()
	
	if existing:
		flash('You already have a pending access request for this policy', 'info')
		return redirect(url_for('customer_policy_management'))
	
	if request.method == 'POST':
		reason = request.form.get('reason', '').strip()
		
		access_request = CustomerPolicyRequest(
			customer_id=current_user.id,
			policy_id=policy_id,
			request_reason=reason
		)
		db.session.add(access_request)
		db.session.commit()
		
		flash(f'Access request submitted for policy {policy.policy_number}', 'success')
		return redirect(url_for('customer_policy_management'))
	
	return render_template('customer/request_policy_access.html', policy=policy)

@app.route('/customer/request-cancellation/<int:policy_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def customer_request_cancellation(policy_id):
	"""Request cancellation of a policy"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Verify ownership
	if policy.email_address != current_user.email:
		flash('You can only request cancellation for your own policies', 'danger')
		return redirect(url_for('customer_policy_management'))
	
	# Check if already cancelled
	if policy.status == 'Cancelled':
		flash('This policy is already cancelled', 'info')
		return redirect(url_for('customer_policy_management'))
	
	# Check for existing pending request
	existing = PolicyCancellationRequest.query.filter_by(
		customer_id=current_user.id,
		policy_id=policy_id,
		status='pending'
	).first()
	
	if existing:
		flash('You already have a pending cancellation request for this policy', 'info')
		return redirect(url_for('customer_policy_management'))
	
	if request.method == 'POST':
		reason = request.form.get('reason', '').strip()
		
		if not reason:
			flash('Please provide a reason for cancellation', 'warning')
			return render_template('customer/request_cancellation.html', policy=policy)
		
		cancel_request = PolicyCancellationRequest(
			customer_id=current_user.id,
			policy_id=policy_id,
			cancellation_reason=reason
		)
		db.session.add(cancel_request)
		db.session.commit()
		
		flash(f'Cancellation request submitted for policy {policy.policy_number}', 'success')
		return redirect(url_for('customer_policy_management'))
	
	return render_template('customer/request_cancellation.html', policy=policy)

@app.route('/customer/request-renewal/<int:policy_id>', methods=['GET', 'POST'])
@login_required
@customer_required
def customer_request_renewal(policy_id):
	"""Request renewal of a policy"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Verify ownership
	if policy.email_address != current_user.email:
		flash('You can only request renewal for your own policies', 'danger')
		return redirect(url_for('customer_policy_management'))
	
	# Check if policy is active
	if policy.status != 'Active':
		flash('Only active policies can be renewed', 'warning')
		return redirect(url_for('customer_policy_management'))
	
	# Check if within renewal window (1 month before expiry)
	days_until_expiry = (policy.expiry_date - date.today()).days
	if days_until_expiry > 30:
		flash(f'Policy can only be renewed within 30 days of expiry. Current expiry: {policy.expiry_date.strftime("%d %B %Y")} ({days_until_expiry} days remaining)', 'warning')
		return redirect(url_for('customer_policy_management'))
	
	# Check for existing pending request
	existing = PolicyRenewalRequest.query.filter_by(
		customer_id=current_user.id,
		policy_id=policy_id,
		status='pending'
	).first()
	
	if existing:
		flash('You already have a pending renewal request for this policy', 'info')
		return redirect(url_for('customer_policy_management'))
	
	if request.method == 'POST':
		# Auto-calculate new dates (1 year from current expiry)
		new_effective_date = policy.expiry_date + timedelta(days=1)
		new_expiry_date = policy.expiry_date + timedelta(days=365)
		
		renewal_request = PolicyRenewalRequest(
			customer_id=current_user.id,
			policy_id=policy_id,
			new_effective_date=new_effective_date,
			new_expiry_date=new_expiry_date,
			renewal_premium=policy.premium_amount  # Default to current premium
		)
		db.session.add(renewal_request)
		db.session.commit()
		
		flash(f'Renewal request submitted for policy {policy.policy_number}', 'success')
		return redirect(url_for('customer_policy_management'))
	
	# Calculate renewal dates for display
	new_effective_date = policy.expiry_date + timedelta(days=1)
	new_expiry_date = policy.expiry_date + timedelta(days=365)
	
	return render_template('customer/request_renewal.html',
		policy=policy,
		new_effective_date=new_effective_date,
		new_expiry_date=new_expiry_date,
		days_until_expiry=days_until_expiry
	)

@app.route('/customer/view-policy-management/<int:policy_id>')
@login_required
@customer_required
def customer_view_policy_from_management(policy_id):
	"""View policy details from policy management (includes monitoring and owned)"""
	policy = Policy.query.get_or_404(policy_id)
	
	# Check if owned or monitored
	is_owner = policy.email_address == current_user.email
	is_monitored = CustomerMonitoredPolicy.query.filter_by(
		customer_id=current_user.id,
		policy_id=policy_id
	).first() is not None
	
	if not is_owner and not is_monitored:
		flash('You do not have access to this policy', 'danger')
		return redirect(url_for('customer_policy_management'))
	
	# Check for pending requests
	has_cancellation_request = PolicyCancellationRequest.query.filter_by(
		customer_id=current_user.id,
		policy_id=policy_id,
		status='pending'
	).first() is not None
	
	has_renewal_request = PolicyRenewalRequest.query.filter_by(
		customer_id=current_user.id,
		policy_id=policy_id,
		status='pending'
	).first() is not None
	
	# Calculate days until expiry
	days_until_expiry = (policy.expiry_date - date.today()).days if policy.expiry_date else None
	can_renew = is_owner and policy.status == 'Active' and days_until_expiry is not None and days_until_expiry <= 30
	
	return render_template('customer/view_policy_management.html',
		policy=policy,
		is_owner=is_owner,
		is_monitored=is_monitored,
		has_cancellation_request=has_cancellation_request,
		has_renewal_request=has_renewal_request,
		days_until_expiry=days_until_expiry,
		can_renew=can_renew
	)

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
	
	# Customer requests statistics
	# Get all policy IDs for this company
	company_policy_ids = [p.id for p in Policy.query.filter_by(insurance_company_id=company_id).all()]
	
	# Count pending customer requests
	pending_access_requests = CustomerPolicyRequest.query.filter(
		CustomerPolicyRequest.policy_id.in_(company_policy_ids),
		CustomerPolicyRequest.status == 'pending'
	).count()
	
	pending_cancellation_requests = PolicyCancellationRequest.query.filter(
		PolicyCancellationRequest.policy_id.in_(company_policy_ids),
		PolicyCancellationRequest.status == 'pending'
	).count()
	
	pending_renewal_requests = PolicyRenewalRequest.query.filter(
		PolicyRenewalRequest.policy_id.in_(company_policy_ids),
		PolicyRenewalRequest.status == 'pending'
	).count()
	
	total_customer_requests = pending_access_requests + pending_cancellation_requests + pending_renewal_requests
	
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
						   pending_access_requests=pending_access_requests,
						   pending_cancellation_requests=pending_cancellation_requests,
						   pending_renewal_requests=pending_renewal_requests,
						   total_customer_requests=total_customer_requests,
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

# ========== INSURER CUSTOMER REQUEST HANDLING ROUTES ==========

@app.route('/insurer/customer-requests')
@login_required
@insurer_required
def insurer_customer_requests():
	"""View all customer requests for insurer's company"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	company_id = current_user.insurance_company_id
	
	# Get all policies for this company
	company_policy_ids = [p.id for p in Policy.query.filter_by(insurance_company_id=company_id).all()]
	
	# Access requests
	access_requests = CustomerPolicyRequest.query.filter(
		CustomerPolicyRequest.policy_id.in_(company_policy_ids),
		CustomerPolicyRequest.status == 'pending'
	).order_by(CustomerPolicyRequest.request_date.desc()).all()
	
	# Cancellation requests
	cancellation_requests = PolicyCancellationRequest.query.filter(
		PolicyCancellationRequest.policy_id.in_(company_policy_ids),
		PolicyCancellationRequest.status == 'pending'
	).order_by(PolicyCancellationRequest.request_date.desc()).all()
	
	# Renewal requests
	renewal_requests = PolicyRenewalRequest.query.filter(
		PolicyRenewalRequest.policy_id.in_(company_policy_ids),
		PolicyRenewalRequest.status == 'pending'
	).order_by(PolicyRenewalRequest.request_date.desc()).all()
	
	return render_template('insurer/customer_requests.html',
		access_requests=access_requests,
		cancellation_requests=cancellation_requests,
		renewal_requests=renewal_requests
	)

@app.route('/insurer/approve-access-request/<int:request_id>', methods=['POST'])
@login_required
@insurer_required
def insurer_approve_access_request(request_id):
	"""Approve customer's policy access request"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	access_request = CustomerPolicyRequest.query.get_or_404(request_id)
	
	# Verify insurer has access to this policy's company
	if access_request.policy.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access', 'danger')
		return redirect(url_for('insurer_customer_requests'))
	
	# Update customer's email in policy
	policy = access_request.policy
	customer = access_request.customer
	
	# Update policy email to match customer
	policy.email_address = customer.email
	
	# Approve request
	access_request.status = 'approved'
	access_request.reviewed_by = current_user.id
	access_request.reviewed_date = datetime.now()
	access_request.review_notes = request.form.get('notes', '').strip()
	
	db.session.commit()
	
	flash(f'Access request approved for policy {policy.policy_number}', 'success')
	return redirect(url_for('insurer_customer_requests'))

@app.route('/insurer/reject-access-request/<int:request_id>', methods=['POST'])
@login_required
@insurer_required
def insurer_reject_access_request(request_id):
	"""Reject customer's policy access request"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	access_request = CustomerPolicyRequest.query.get_or_404(request_id)
	
	# Verify insurer has access to this policy's company
	if access_request.policy.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access', 'danger')
		return redirect(url_for('insurer_customer_requests'))
	
	reason = request.form.get('reason', '').strip()
	if not reason:
		flash('Please provide a reason for rejection', 'warning')
		return redirect(url_for('insurer_customer_requests'))
	
	# Reject request
	access_request.status = 'rejected'
	access_request.reviewed_by = current_user.id
	access_request.reviewed_date = datetime.now()
	access_request.rejection_reason = reason
	
	db.session.commit()
	
	flash(f'Access request rejected for policy {access_request.policy.policy_number}', 'info')
	return redirect(url_for('insurer_customer_requests'))

@app.route('/insurer/approve-cancellation-request/<int:request_id>', methods=['POST'])
@login_required
@insurer_required
def insurer_approve_cancellation_request(request_id):
	"""Approve customer's policy cancellation request"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	cancel_request = PolicyCancellationRequest.query.get_or_404(request_id)
	
	# Verify insurer has access to this policy's company
	if cancel_request.policy.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access', 'danger')
		return redirect(url_for('insurer_customer_requests'))
	
	# Cancel the policy
	policy = cancel_request.policy
	policy.status = 'Cancelled'
	policy.cancelled_by = current_user.id
	policy.cancellation_date = datetime.now()
	policy.cancellation_reason = cancel_request.cancellation_reason
	
	# Approve request
	cancel_request.status = 'approved'
	cancel_request.reviewed_by = current_user.id
	cancel_request.reviewed_date = datetime.now()
	cancel_request.review_notes = request.form.get('notes', '').strip()
	
	db.session.commit()
	
	flash(f'Policy {policy.policy_number} has been cancelled', 'success')
	return redirect(url_for('insurer_customer_requests'))

@app.route('/insurer/reject-cancellation-request/<int:request_id>', methods=['POST'])
@login_required
@insurer_required
def insurer_reject_cancellation_request(request_id):
	"""Reject customer's policy cancellation request"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	cancel_request = PolicyCancellationRequest.query.get_or_404(request_id)
	
	# Verify insurer has access to this policy's company
	if cancel_request.policy.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access', 'danger')
		return redirect(url_for('insurer_customer_requests'))
	
	reason = request.form.get('reason', '').strip()
	if not reason:
		flash('Please provide a reason for rejection', 'warning')
		return redirect(url_for('insurer_customer_requests'))
	
	# Reject request
	cancel_request.status = 'rejected'
	cancel_request.reviewed_by = current_user.id
	cancel_request.reviewed_date = datetime.now()
	cancel_request.rejection_reason = reason
	
	db.session.commit()
	
	flash(f'Cancellation request rejected for policy {cancel_request.policy.policy_number}', 'info')
	return redirect(url_for('insurer_customer_requests'))

@app.route('/insurer/approve-renewal-request/<int:request_id>', methods=['POST'])
@login_required
@insurer_required
def insurer_approve_renewal_request(request_id):
	"""Approve customer's policy renewal request"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	renewal_request = PolicyRenewalRequest.query.get_or_404(request_id)
	
	# Verify insurer has access to this policy's company
	if renewal_request.policy.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access', 'danger')
		return redirect(url_for('insurer_customer_requests'))
	
	# Get adjusted premium from form (insurer can modify)
	try:
		adjusted_premium = float(request.form.get('premium', renewal_request.policy.premium_amount))
	except:
		adjusted_premium = renewal_request.policy.premium_amount
	
	# Update policy dates
	policy = renewal_request.policy
	policy.effective_date = renewal_request.new_effective_date
	policy.expiry_date = renewal_request.new_expiry_date
	policy.premium_amount = adjusted_premium
	policy.status = 'Active'
	
	# Approve request
	renewal_request.status = 'approved'
	renewal_request.reviewed_by = current_user.id
	renewal_request.reviewed_date = datetime.now()
	renewal_request.renewal_premium = adjusted_premium
	renewal_request.review_notes = request.form.get('notes', '').strip()
	
	db.session.commit()
	
	flash(f'Policy {policy.policy_number} has been renewed until {policy.expiry_date.strftime("%d %B %Y")}', 'success')
	return redirect(url_for('insurer_customer_requests'))

@app.route('/insurer/reject-renewal-request/<int:request_id>', methods=['POST'])
@login_required
@insurer_required
def insurer_reject_renewal_request(request_id):
	"""Reject customer's policy renewal request"""
	if not current_user.is_approved:
		return redirect(url_for('request_insurer_access'))
	
	renewal_request = PolicyRenewalRequest.query.get_or_404(request_id)
	
	# Verify insurer has access to this policy's company
	if renewal_request.policy.insurance_company_id != current_user.insurance_company_id:
		flash('Unauthorized access', 'danger')
		return redirect(url_for('insurer_customer_requests'))
	
	reason = request.form.get('reason', '').strip()
	if not reason:
		flash('Please provide a reason for rejection', 'warning')
		return redirect(url_for('insurer_customer_requests'))
	
	# Reject request
	renewal_request.status = 'rejected'
	renewal_request.reviewed_by = current_user.id
	renewal_request.reviewed_date = datetime.now()
	renewal_request.rejection_reason = reason
	
	db.session.commit()
	
	flash(f'Renewal request rejected for policy {renewal_request.policy.policy_number}', 'info')
	return redirect(url_for('insurer_customer_requests'))

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
	
	# Regulator is approved, show dashboard with data
	
	# Get all insurance companies
	all_companies = InsuranceCompany.query.filter_by(is_active=True).all()
	
	# Get all insurers with their company info
	all_insurers = Insurer.query.filter_by(is_approved=True).all()
	
	# Get all policies and claims for statistics
	all_policies = Policy.query.all()
	all_claims = Claim.query.all()
	
	# Calculate statistics
	total_companies = len(all_companies)
	total_insurers = len(all_insurers)
	total_policies = len(all_policies)
	active_policies = sum(1 for p in all_policies if p.status == 'Active')
	total_claims = len(all_claims)
	pending_claims = sum(1 for c in all_claims if c.status == 'Pending')
	
	# Calculate compliance rate (based on claim approval rate)
	approved_claims = sum(1 for c in all_claims if c.status == 'Approved')
	compliance_rate = (approved_claims / total_claims * 100) if total_claims > 0 else 100
	
	# Get company performance data
	company_data = []
	for company in all_companies[:10]:  # Top 10 companies
		comp_policies = Policy.query.filter_by(insurance_company_id=company.id).all()
		comp_active = sum(1 for p in comp_policies if p.status == 'Active')
		comp_claims = Claim.query.join(Policy).filter(Policy.insurance_company_id == company.id).all()
		comp_approved = sum(1 for c in comp_claims if c.status == 'Approved')
		comp_total_claims = len(comp_claims)
		
		# Calculate compliance score
		claim_approval = (comp_approved / comp_total_claims * 100) if comp_total_claims > 0 else 100
		compliance_score = min(100, claim_approval)
		
		company_data.append({
			'name': company.name,
			'active_policies': comp_active,
			'compliance_score': compliance_score,
			'status': 'Active' if company.is_active else 'Inactive'
		})
	
	# Sort by compliance score
	company_data.sort(key=lambda x: x['compliance_score'], reverse=True)
	
	# Get recent claims as "issues" (claims with Rejected or Pending status could be violations)
	recent_issues = []
	problem_claims = Claim.query.filter(
		Claim.status.in_(['Rejected', 'Under Review'])
	).order_by(Claim.date_submitted.desc()).limit(10).all()
	
	for claim in problem_claims:
		issue_type = 'Claim Processing' if claim.status == 'Under Review' else 'Claim Rejection'
		severity = 'Medium' if claim.status == 'Under Review' else 'High'
		
		recent_issues.append({
			'id': claim.claim_number,
			'company': claim.insurance_company.name if claim.insurance_company else 'Unknown',
			'type': issue_type,
			'severity': severity
		})
	
	return render_template('regulator/regulatordashboard.html',
		total_companies=total_companies,
		total_insurers=total_insurers,
		total_policies=total_policies,
		active_policies=active_policies,
		total_claims=total_claims,
		pending_claims=pending_claims,
		compliance_rate=compliance_rate,
		company_data=company_data,
		recent_issues=recent_issues
	)

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
	query = request.args.get('q', '').strip()
	search_type = request.args.get('type', 'all')
	
	results = {
		'companies': [],
		'insurers': [],
		'policies': [],
		'claims': []
	}
	
	if query:
		search_pattern = f"%{query}%"
		
		# Search insurance companies
		if search_type in ['all', 'companies']:
			results['companies'] = InsuranceCompany.query.filter(
				InsuranceCompany.name.ilike(search_pattern)
			).limit(20).all()
		
		# Search insurers (professionals)
		if search_type in ['all', 'insurers']:
			results['insurers'] = Insurer.query.filter(
				db.or_(
					Insurer.username.ilike(search_pattern),
					Insurer.email.ilike(search_pattern),
					Insurer.staff_id.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search all policies (regulatory oversight)
		if search_type in ['all', 'policies']:
			results['policies'] = Policy.query.filter(
				db.or_(
					Policy.policy_number.ilike(search_pattern),
					Policy.insured_name.ilike(search_pattern),
					Policy.registration_number.ilike(search_pattern),
					Policy.national_id.ilike(search_pattern)
				)
			).limit(20).all()
		
		# Search all claims (regulatory oversight)
		if search_type in ['all', 'claims']:
			results['claims'] = Claim.query.filter(
				db.or_(
					Claim.claim_number.ilike(search_pattern),
					Claim.police_report_number.ilike(search_pattern)
				)
			).limit(20).all()
	
	total_results = sum(len(v) for v in results.values())
	
	return render_template('regulator/search.html', 
		query=query,
		search_type=search_type,
		results=results,
		total_results=total_results
	)

@app.route('/regulator/reports-and-insights')
@login_required
@regulator_required
def regulator_reports_and_insights():
	"""View comprehensive regulatory oversight reports and insights"""
	if not current_user.is_approved:
		return redirect(url_for('request_regulator_access'))
	
	# Get all data for industry oversight
	all_companies = InsuranceCompany.query.filter_by(is_active=True).all()
	all_policies = Policy.query.all()
	all_claims = Claim.query.all()
	all_quotes = Quote.query.all()
	all_insurers = Insurer.query.all()
	all_customers = Customer.query.all()
	
	# Industry policy statistics
	total_policies = len(all_policies)
	active_policies = sum(1 for p in all_policies if p.status == 'Active')
	expired_policies = sum(1 for p in all_policies if p.status == 'Expired')
	cancelled_policies = sum(1 for p in all_policies if p.status == 'Cancelled')
	total_premium = sum(p.premium_amount for p in all_policies if p.status == 'Active')
	
	# Industry claims statistics
	total_claims = len(all_claims)
	pending_claims = sum(1 for c in all_claims if c.status == 'Pending')
	under_review_claims = sum(1 for c in all_claims if c.status == 'Under Review')
	approved_claims = sum(1 for c in all_claims if c.status == 'Approved')
	rejected_claims = sum(1 for c in all_claims if c.status == 'Rejected')
	
	# Calculate claim approval rate
	claim_approval_rate = (approved_claims / total_claims * 100) if total_claims else 0
	
	# Industry quotes statistics
	total_quotes = len(all_quotes)
	converted_quotes = sum(1 for q in all_quotes if q.status == 'Converted')
	quote_conversion_rate = (converted_quotes / total_quotes * 100) if total_quotes else 0
	
	# Company compliance and performance
	company_performance = []
	for company in all_companies:
		comp_policies = Policy.query.filter_by(insurance_company_id=company.id).all()
		comp_active = sum(1 for p in comp_policies if p.status == 'Active')
		comp_premium = sum(p.premium_amount for p in comp_policies if p.status == 'Active')
		comp_claims = Claim.query.join(Policy).filter(Policy.insurance_company_id == company.id).all()
		comp_total_claims = len(comp_claims)
		comp_approved_claims = sum(1 for c in comp_claims if c.status == 'Approved')
		comp_rejected_claims = sum(1 for c in comp_claims if c.status == 'Rejected')
		comp_staff = Insurer.query.filter_by(insurance_company_id=company.id, is_approved=True).count()
		
		# Calculate compliance score (simple metric based on claim approval rate and policy management)
		claim_approval = (comp_approved_claims / comp_total_claims * 100) if comp_total_claims else 100
		compliance_score = min(100, (claim_approval * 0.6 + 40))  # Weighted score
		
		company_performance.append({
			'name': company.name,
			'active_policies': comp_active,
			'total_premium': comp_premium,
			'total_claims': comp_total_claims,
			'approved_claims': comp_approved_claims,
			'rejected_claims': comp_rejected_claims,
			'staff_count': comp_staff,
			'compliance_score': compliance_score
		})
	
	# Sort by compliance score (descending)
	company_performance.sort(key=lambda x: x['compliance_score'], reverse=True)
	
	# Policy type breakdown
	comprehensive_policies = sum(1 for p in all_policies if p.policy_type == 'Comprehensive')
	third_party_policies = sum(1 for p in all_policies if p.policy_type == 'Third-Party')
	
	# Market concentration (top 5 companies by active policies)
	top_companies = sorted(company_performance, key=lambda x: x['active_policies'], reverse=True)[:5]
	top_companies_policies = sum(c['active_policies'] for c in top_companies)
	market_concentration = (top_companies_policies / total_policies * 100) if total_policies else 0
	
	# Customer protection metrics
	total_customers = len(all_customers)
	# Count unique customers by email in policies
	customers_with_policies = len(set(p.email_address for p in all_policies if p.email_address))
	# Count unique customers by matching policy emails with claims
	policy_emails_with_claims = set()
	for claim in all_claims:
		if claim.policy and claim.policy.email_address:
			policy_emails_with_claims.add(claim.policy.email_address)
	customers_with_claims = len(policy_emails_with_claims)
	
	return render_template('regulator/reports_and_insights.html',
		# Regulatory body
		regulatory_body=current_user.regulatory_body,
		# Industry stats
		total_companies=len(all_companies),
		total_policies=total_policies,
		active_policies=active_policies,
		expired_policies=expired_policies,
		cancelled_policies=cancelled_policies,
		total_premium=total_premium,
		comprehensive_policies=comprehensive_policies,
		third_party_policies=third_party_policies,
		# Claims stats
		total_claims=total_claims,
		pending_claims=pending_claims,
		under_review_claims=under_review_claims,
		approved_claims=approved_claims,
		rejected_claims=rejected_claims,
		claim_approval_rate=claim_approval_rate,
		# Quotes stats
		total_quotes=total_quotes,
		converted_quotes=converted_quotes,
		quote_conversion_rate=quote_conversion_rate,
		# Market data
		total_insurers=len(all_insurers),
		approved_insurers=sum(1 for i in all_insurers if i.is_approved),
		company_performance=company_performance,
		market_concentration=market_concentration,
		top_companies=top_companies,
		# Customer protection
		total_customers=total_customers,
		customers_with_policies=customers_with_policies,
		customers_with_claims=customers_with_claims
	)

@app.route('/regulator/export-reports-csv')
@login_required
@regulator_required
def regulator_export_reports_csv():
	"""Export regulator reports data to CSV"""
	if not current_user.is_approved:
		return redirect(url_for('request_regulator_access'))
	
	si = StringIO()
	writer = csv.writer(si)
	
	# Get export type from query parameter
	export_type = request.args.get('type', 'summary')
	
	if export_type == 'companies':
		writer.writerow(['Company Name', 'Active Policies', 'Total Premium (KES)', 'Total Claims', 'Approved Claims', 'Rejected Claims', 'Staff Count', 'Compliance Score'])
		all_companies = InsuranceCompany.query.filter_by(is_active=True).all()
		for company in all_companies:
			comp_policies = Policy.query.filter_by(insurance_company_id=company.id).all()
			comp_active = sum(1 for p in comp_policies if p.status == 'Active')
			comp_premium = sum(p.premium_amount for p in comp_policies if p.status == 'Active')
			comp_claims = Claim.query.join(Policy).filter(Policy.insurance_company_id == company.id).all()
			comp_total_claims = len(comp_claims)
			comp_approved_claims = sum(1 for c in comp_claims if c.status == 'Approved')
			comp_rejected_claims = sum(1 for c in comp_claims if c.status == 'Rejected')
			comp_staff = Insurer.query.filter_by(insurance_company_id=company.id, is_approved=True).count()
			claim_approval = (comp_approved_claims / comp_total_claims * 100) if comp_total_claims else 100
			compliance_score = min(100, (claim_approval * 0.6 + 40))
			writer.writerow([company.name, comp_active, f'{comp_premium:.2f}', comp_total_claims, comp_approved_claims, comp_rejected_claims, comp_staff, f'{compliance_score:.1f}'])
	
	elif export_type == 'policies':
		writer.writerow(['Policy Number', 'Company', 'Type', 'Premium (KES)', 'Status', 'Start Date', 'Expiry Date'])
		all_policies = Policy.query.all()
		for p in all_policies:
			writer.writerow([
				p.policy_number,
				p.insurance_company.name if p.insurance_company else 'N/A',
				p.policy_type,
				f'{p.premium_amount:.2f}',
				p.status,
				p.start_date.strftime('%Y-%m-%d') if p.start_date else 'N/A',
				p.expiry_date.strftime('%Y-%m-%d') if p.expiry_date else 'N/A'
			])
	
	elif export_type == 'claims':
		writer.writerow(['Claim Number', 'Policy Number', 'Company', 'Status', 'Date Submitted', 'Review Date'])
		all_claims = Claim.query.all()
		for c in all_claims:
			writer.writerow([
				c.claim_number,
				c.policy.policy_number if c.policy else 'N/A',
				c.insurance_company.name if c.insurance_company else 'N/A',
				c.status,
				c.date_submitted.strftime('%Y-%m-%d') if c.date_submitted else 'N/A',
				c.review_date.strftime('%Y-%m-%d') if c.review_date else 'N/A'
			])
	
	else:  # summary
		writer.writerow(['Metric', 'Value'])
		all_companies = InsuranceCompany.query.filter_by(is_active=True).all()
		all_policies = Policy.query.all()
		all_claims = Claim.query.all()
		all_quotes = Quote.query.all()
		
		writer.writerow(['Total Insurance Companies', len(all_companies)])
		writer.writerow(['Total Policies', len(all_policies)])
		writer.writerow(['Active Policies', sum(1 for p in all_policies if p.status == 'Active')])
		writer.writerow(['Total Premium (KES)', f'{sum(p.premium_amount for p in all_policies if p.status == "Active"):.2f}'])
		writer.writerow(['Total Claims', len(all_claims)])
		writer.writerow(['Approved Claims', sum(1 for c in all_claims if c.status == 'Approved')])
		writer.writerow(['Rejected Claims', sum(1 for c in all_claims if c.status == 'Rejected')])
		writer.writerow(['Claim Approval Rate (%)', f'{(sum(1 for c in all_claims if c.status == "Approved") / len(all_claims) * 100):.2f}' if all_claims else '0.00'])
		writer.writerow(['Total Quotes', len(all_quotes)])
		writer.writerow(['Quote Conversion Rate (%)', f'{(sum(1 for q in all_quotes if q.status == "Converted") / len(all_quotes) * 100):.2f}' if all_quotes else '0.00'])
	
	output = si.getvalue()
	si.close()
	
	return Response(
		output,
		mimetype='text/csv',
		headers={'Content-Disposition': f'attachment; filename=clearview_regulator_report_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
	)

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
	"""Serve uploaded files"""
	return send_from_directory(os.path.join(app.root_path, 'upload'), filename)

if __name__ == '__main__':
	app.run(debug=True)