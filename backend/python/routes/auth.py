from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models.database import db, User, Student, Message

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def role_select():
    """Landing page — unified login."""
    if current_user.is_authenticated:
        return _redirect_by_role()
    return render_template('login.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def unified_login():
    """Unified login — auto-detects role from credentials."""
    if current_user.is_authenticated:
        return _redirect_by_role()

    if request.method == 'GET':
        return render_template('login.html')

    # POST — attempt auto-detection login
    identifier = request.form.get('identifier', '').strip()
    password = request.form.get('password', '')

    if not identifier or not password:
        flash('Please enter your Username/Register Number and Password.', 'error')
        return render_template('login.html')

    # 1. Try Student login (match by reg_no)
    student = Student.query.filter_by(reg_no=identifier).first()
    if student and student.check_password(password):
        student.id_with_prefix = f'student_{student.id}'
        login_user(student)
        session['user_type'] = 'student'
        session['user_role'] = 'student'
        flash(f'Welcome, {student.name}!', 'success')
        return redirect(url_for('dashboard.student_dashboard'))

    # 2. Try Admin/Staff login (match by username)
    user = User.query.filter_by(username=identifier).first()
    if user and user.check_password(password):
        user.id_with_prefix = f'user_{user.id}'
        login_user(user)
        session['user_type'] = 'user'
        session['user_role'] = user.role
        flash(f'Welcome, {user.username}!', 'success')
        if user.role == 'admin':
            return redirect(url_for('dashboard.admin_dashboard'))
        else:
            return redirect(url_for('dashboard.staff_dashboard'))

    # 3. No match
    flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')



# Keep old per-role login for backward compatibility
@auth_bp.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    """Legacy per-role login page."""
    if role not in ('admin', 'staff', 'student'):
        flash('Invalid role selected.', 'error')
        return redirect(url_for('auth.role_select'))

    if current_user.is_authenticated:
        return _redirect_by_role()

    if request.method == 'POST':
        if role == 'student':
            reg_no = request.form.get('reg_no', '').strip()
            password = request.form.get('password', '')

            if not reg_no or not password:
                flash('Please enter Register Number and Password.', 'error')
                return render_template('login_form.html', role=role)

            student = Student.query.filter_by(reg_no=reg_no).first()

            if student and student.check_password(password):
                student.id_with_prefix = f'student_{student.id}'
                login_user(student)
                session['user_type'] = 'student'
                session['user_role'] = 'student'
                flash(f'Welcome, {student.name}!', 'success')
                return redirect(url_for('dashboard.student_dashboard'))
            else:
                flash('Invalid Register Number or Password.', 'error')

        else:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                flash('Please enter Username and Password.', 'error')
                return render_template('login_form.html', role=role)

            user = User.query.filter_by(username=username, role=role).first()

            if user and user.check_password(password):
                user.id_with_prefix = f'user_{user.id}'
                login_user(user)
                session['user_type'] = 'user'
                session['user_role'] = role
                flash(f'Welcome, {user.username}!', 'success')
                if role == 'admin':
                    return redirect(url_for('dashboard.admin_dashboard'))
                else:
                    return redirect(url_for('dashboard.staff_dashboard'))
            else:
                flash('Invalid Username or Password.', 'error')

    return render_template('login_form.html', role=role)


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    session.clear()
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.role_select'))


def _redirect_by_role():
    """Redirect authenticated user to their dashboard."""
    role = session.get('user_role', '')
    if role == 'admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif role == 'staff':
        return redirect(url_for('dashboard.staff_dashboard'))
    elif role == 'student':
        return redirect(url_for('dashboard.student_dashboard'))
    return redirect(url_for('auth.role_select'))
