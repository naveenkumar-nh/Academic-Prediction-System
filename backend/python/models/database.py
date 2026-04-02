from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for Admin and Staff authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # 'admin' or 'staff'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return f'user_{self.id}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Student(UserMixin, db.Model):
    """Student model — login with reg_no + password."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    dept = db.Column(db.String(100), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    academics = db.relationship('StudentAcademic', backref='student', lazy=True)
    creator = db.relationship('User', backref='students_created')

    def get_id(self):
        return f'student_{self.id}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Student {self.name} ({self.reg_no})>'


class StudentAcademic(db.Model):
    """Student academic records — marks & prediction results."""
    __tablename__ = 'student_academics'

    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(50), db.ForeignKey('students.reg_no'), nullable=False, index=True)

    # Internal marks
    internal_1 = db.Column(db.Float, nullable=False, default=0)
    internal_2 = db.Column(db.Float, nullable=False, default=0)
    internal_3 = db.Column(db.Float, nullable=False, default=0)
    assignment = db.Column(db.Float, nullable=False, default=0)

    # Previous performance
    prev_sem_gpa = db.Column(db.Float, nullable=False, default=0)

    # Study habits
    study_hours_per_day = db.Column(db.Float, nullable=False, default=0)

    # Extra activities
    extra_activity = db.Column(db.Boolean, nullable=False, default=False)
    extra_activity_type = db.Column(db.String(100), nullable=True)

    # Attendance
    attendance = db.Column(db.Float, nullable=False, default=0)  # 0-100%

    # Prediction output
    prediction_result = db.Column(db.String(20), nullable=True, index=True)  # Pass / Fail
    risk_level = db.Column(db.String(20), nullable=True, index=True)  # Low / Medium / High

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def internal_avg(self):
        """Calculate average of internal marks."""
        return round((self.internal_1 + self.internal_2 + self.internal_3) / 3, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'reg_no': self.reg_no,
            'internal_1': self.internal_1,
            'internal_2': self.internal_2,
            'internal_3': self.internal_3,
            'assignment': self.assignment,
            'internal_avg': self.internal_avg(),
            'prev_sem_gpa': self.prev_sem_gpa,
            'study_hours_per_day': self.study_hours_per_day,
            'extra_activity': self.extra_activity,
            'extra_activity_type': self.extra_activity_type,
            'attendance': self.attendance,
            'prediction_result': self.prediction_result,
            'risk_level': self.risk_level,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

    def __repr__(self):
        return f'<StudentAcademic {self.reg_no}>'


class PredictionHistory(db.Model):
    """Stores each prediction run for tracking progress over time."""
    __tablename__ = 'prediction_history'

    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(50), db.ForeignKey('students.reg_no'), nullable=False, index=True)
    prediction_result = db.Column(db.String(20), nullable=False)  # Pass / Fail
    risk_level = db.Column(db.String(20), nullable=False)         # Low / Medium / High
    grade = db.Column(db.String(5), nullable=False)               # A+ / A / B / C / D / F
    internal_avg = db.Column(db.Float, nullable=False, default=0)
    attendance = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='prediction_history')

    def __repr__(self):
        return f'<PredictionHistory {self.reg_no} {self.prediction_result}>'


class Message(db.Model):
    """Messages between students and staff."""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_type = db.Column(db.String(10), nullable=False)  # 'student' or 'staff'
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_type = db.Column(db.String(10), nullable=False)  # 'student' or 'staff'
    receiver_id = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def __repr__(self):
        return f'<Message {self.id} {self.sender_type}:{self.sender_id} -> {self.receiver_type}:{self.receiver_id}>'
