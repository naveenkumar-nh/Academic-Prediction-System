import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'academic-prediction-secret-key-2026')

    # Prefer managed DB in production (Render Postgres, Railway, etc.)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # SQLAlchemy expects postgresql:// instead of postgres://
        SQLALCHEMY_DATABASE_URI = database_url.replace('postgres://', 'postgresql://', 1)
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'academic.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
