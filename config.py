
import os

class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key'
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	# Flask-Caching defaults
	CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache')
	CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))
