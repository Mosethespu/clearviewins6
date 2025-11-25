
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

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
