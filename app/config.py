import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEBUG = True

SECRET_KEY = '123456789'
DATABASE_FILE = 'UserDatabase.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, DATABASE_FILE))
DATABASE_CONNECT_OPTIONS = {}

#INTERNAL_URL = 'http://192.168.142.136:5000/'

#UPLOAD_FOLDER = "{}".format(os.path.join(BASE_DIR, 'uploads/'))

SQLALCHEMY_TRACK_MODIFICATIONS = False

