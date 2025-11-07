from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class CustomerSignupForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')

class InsurerSignupForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	staff_id = StringField('Staff ID', validators=[DataRequired(), Length(min=3, max=64)])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')

class RegulatorSignupForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	staff_id = StringField('Staff ID', validators=[DataRequired(), Length(min=3, max=64)])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	submit = SubmitField('Log In')
