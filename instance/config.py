import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "supergeheim"
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'datenbank.sqlite')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

