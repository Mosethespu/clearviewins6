
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
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
