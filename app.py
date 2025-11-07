from flask import Flask, render_template

app = Flask(__name__)

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

@app.route('/auth/login')
def login():
	return render_template('login.html')

@app.route('/auth/signup')
def signup():
	return render_template('signup.html')

@app.route('/forgotpassword')
def forgot_password():
	return render_template('forgotpassword.html')

if __name__ == '__main__':
	app.run(debug=True)