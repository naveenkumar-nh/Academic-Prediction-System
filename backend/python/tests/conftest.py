"""
Pytest fixtures for Academic Prediction System tests.
"""

import sys
import os
import pytest

# Add parent directory to path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models.database import db as _db, User, Student, StudentAcademic


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    os.environ['TESTING'] = 'true'
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['LOGIN_DISABLED'] = False

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Create fresh database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        # Clean tables
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app, db):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_admin(db):
    """Create a sample admin user."""
    admin = User(username='testadmin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def sample_staff(db):
    """Create a sample staff user."""
    staff = User(username='teststaff', role='staff')
    staff.set_password('staff123')
    db.session.add(staff)
    db.session.commit()
    return staff


@pytest.fixture
def sample_student(db, sample_staff):
    """Create a sample student."""
    student = Student(
        reg_no='2024CSE001',
        name='Test Student',
        dept='CSE',
        year=2,
        created_by=sample_staff.id
    )
    student.set_password('student123')
    db.session.add(student)
    db.session.commit()
    return student


@pytest.fixture
def sample_academic(db, sample_student):
    """Create sample academic data for a student."""
    academic = StudentAcademic(
        reg_no=sample_student.reg_no,
        internal_1=75.0,
        internal_2=80.0,
        internal_3=70.0,
        assignment=25.0,
        prev_sem_gpa=8.0,
        study_hours_per_day=3.0,
        extra_activity=True,
        extra_activity_type='Sports',
        attendance=85.0
    )
    db.session.add(academic)
    db.session.commit()
    return academic
