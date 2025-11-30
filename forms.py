
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateField, FloatField, IntegerField, BooleanField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange

class SignupForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	user_type = SelectField('User Type', choices=[('customer', 'Customer'), ('insurer', 'Insurer'), ('regulator', 'Regulator')], validators=[DataRequired()])
	staff_id = StringField('Staff ID', validators=[Optional()])
	submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	submit = SubmitField('Log In')

class InsurerAccessRequestForm(FlaskForm):
	staff_id = StringField('Staff ID', validators=[DataRequired(), Length(min=3, max=50)])
	insurance_company = SelectField('Insurance Company', coerce=int, validators=[DataRequired()])
	submit = SubmitField('Request Access')

class RegulatorAccessRequestForm(FlaskForm):
	staff_id = StringField('Staff ID', validators=[DataRequired(), Length(min=3, max=50)])
	regulatory_body = SelectField('Regulatory Body', coerce=int, validators=[DataRequired()])
	submit = SubmitField('Request Access')

class ReviewRequestForm(FlaskForm):
	rejection_reason = TextAreaField('Rejection Reason (if rejecting)', validators=[Optional()])
	submit = SubmitField('Submit')

class PolicyCreationForm(FlaskForm):
	# Section A: Policy Information
	policy_type = SelectField('Policy Type', 
		choices=[('Comprehensive', 'Comprehensive'), 
				 ('Third-Party Only', 'Third-Party Only'), 
				 ('Third-Party, Fire & Theft', 'Third-Party, Fire & Theft')],
		validators=[DataRequired()])
	effective_date = DateField('Effective Date', validators=[DataRequired()])
	premium_amount = FloatField('Premium Amount (KES)', validators=[DataRequired(), NumberRange(min=0)])
	payment_mode = SelectField('Payment Mode',
		choices=[('Mobile Money', 'Mobile Money'), 
				 ('Bank Transfer', 'Bank Transfer'), 
				 ('Credit/Debit Card', 'Credit/Debit Card')],
		validators=[DataRequired()])
	
	# Section B: Insured Details
	insured_name = StringField('Full Name', validators=[DataRequired(), Length(max=200)])
	national_id = StringField('National ID / Passport Number', validators=[DataRequired(), Length(max=50)])
	kra_pin = StringField('KRA PIN', validators=[Optional(), Length(max=50)])
	date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
	phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
	email_address = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=150)])
	postal_address = TextAreaField('Postal Address', validators=[Optional()])
	
	# Section C: Vehicle Details
	registration_number = StringField('Registration Number (Plate)', validators=[DataRequired(), Length(max=50)])
	make_model = StringField('Make & Model', validators=[DataRequired(), Length(max=150)])
	year_of_manufacture = IntegerField('Year of Manufacture', validators=[DataRequired(), NumberRange(min=1980, max=2030)])
	chassis_number = StringField('Chassis Number', validators=[DataRequired(), Length(max=100)])
	engine_number = StringField('Engine Number', validators=[DataRequired(), Length(max=100)])
	body_type = SelectField('Body Type',
		choices=[('Saloon', 'Saloon'), ('SUV', 'SUV'), ('Pickup', 'Pickup'), 
				 ('Lorry', 'Lorry'), ('Bus', 'Bus'), ('Motorcycle', 'Motorcycle')],
		validators=[DataRequired()])
	color = StringField('Color', validators=[DataRequired(), Length(max=50)])
	seating_capacity = IntegerField('Seating Capacity', validators=[DataRequired(), NumberRange(min=1)])
	use_category = SelectField('Use Category',
		choices=[('Private', 'Private'), ('Commercial', 'Commercial'), 
				 ('PSV (Taxi/Matatu)', 'PSV (Taxi/Matatu)'), ('Motorcycle', 'Motorcycle')],
		validators=[DataRequired()])
	
	# Section D: Coverage & Add-ons
	sum_insured = FloatField('Sum Insured (KES)', validators=[DataRequired(), NumberRange(min=0)])
	excess = FloatField('Excess (Deductible)', validators=[DataRequired(), NumberRange(min=0)])
	political_violence = BooleanField('Political Violence & Terrorism')
	windscreen_cover = BooleanField('Windscreen Cover')
	passenger_liability = BooleanField('Passenger Liability')
	road_rescue = BooleanField('Road Rescue Services')
	
	# Section F: Vehicle Photos (handled separately with AJAX)
	
	submit = SubmitField('Submit Policy')
