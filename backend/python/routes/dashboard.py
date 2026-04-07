from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_login import login_required, current_user
from models.database import db, User, Student, StudentAcademic, PredictionHistory, Message
from models.ml_model import predict_result
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/api-docs')
def api_docs():
    """Serve the API documentation page."""
    return render_template('api_docs.html')


# ============================================================
#  ADMIN DASHBOARD
# ============================================================

@dashboard_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard — manage staff and students with analytics."""
    if session.get('user_role') != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('auth.role_select'))

    staff_list = User.query.filter_by(role='staff').order_by(User.created_at.desc()).all()
    total_staff = len(staff_list)

    # Load all admin accounts (exclude the current admin)
    admin_list = User.query.filter_by(role='admin').order_by(User.created_at.desc()).all()
    total_admins = len(admin_list)

    # Load all students with academic data
    students = Student.query.order_by(Student.created_at.desc()).all()
    total_students = len(students)
    student_data = []
    for s in students:
        academic = StudentAcademic.query.filter_by(reg_no=s.reg_no).first()
        student_data.append({'student': s, 'academic': academic})

    # --- NEW: Analytics Stats ---
    total_pass = 0
    total_fail = 0
    total_pending = 0
    total_high_risk = 0
    total_medium_risk = 0
    total_low_risk = 0
    dept_stats = {}  # { dept: { students, pass, fail, pending, avg_attendance } }

    for item in student_data:
        s = item['student']
        a = item['academic']
        dept = s.dept

        if dept not in dept_stats:
            dept_stats[dept] = {'students': 0, 'pass': 0, 'fail': 0, 'pending': 0,
                                'total_attendance': 0, 'attendance_count': 0,
                                'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}
        dept_stats[dept]['students'] += 1

        if a and a.prediction_result:
            if a.prediction_result == 'Pass':
                total_pass += 1
                dept_stats[dept]['pass'] += 1
            else:
                total_fail += 1
                dept_stats[dept]['fail'] += 1

            if a.risk_level == 'High':
                total_high_risk += 1
                dept_stats[dept]['high_risk'] += 1
            elif a.risk_level == 'Medium':
                total_medium_risk += 1
                dept_stats[dept]['medium_risk'] += 1
            elif a.risk_level == 'Low':
                total_low_risk += 1
                dept_stats[dept]['low_risk'] += 1
        else:
            total_pending += 1
            dept_stats[dept]['pending'] += 1

        if a and a.attendance:
            dept_stats[dept]['total_attendance'] += a.attendance
            dept_stats[dept]['attendance_count'] += 1

    # Calculate average attendance per dept
    for dept in dept_stats:
        cnt = dept_stats[dept]['attendance_count']
        dept_stats[dept]['avg_attendance'] = round(dept_stats[dept]['total_attendance'] / cnt, 1) if cnt > 0 else 0

    admin_messages = Message.query.filter(
        ((Message.receiver_type == 'admin') & (Message.receiver_id == current_user.id)) |
        ((Message.sender_type == 'admin') & (Message.sender_id == current_user.id))
    ).filter(Message.parent_id == None).order_by(Message.created_at.desc()).all()

    unread_msg_count = Message.query.filter_by(
        receiver_type='admin', receiver_id=current_user.id, is_read=False
    ).count()

    return render_template('admin_dashboard.html',
                           staff_list=staff_list,
                           total_staff=total_staff,
                           admin_list=admin_list,
                           total_admins=total_admins,
                           total_students=total_students,
                           student_data=student_data,
                           total_pass=total_pass,
                           total_fail=total_fail,
                           total_pending=total_pending,
                           total_high_risk=total_high_risk,
                           total_medium_risk=total_medium_risk,
                           total_low_risk=total_low_risk,
                           dept_stats=dept_stats,
                           messages=admin_messages,
                           unread_msg_count=unread_msg_count)


@dashboard_bp.route('/admin/add-staff', methods=['POST'])
@login_required
def add_staff():
    """Admin adds a new staff member."""
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        flash('Username and Password are required.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    if len(password) < 4:
        flash('Password must be at least 4 characters.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    staff = User(username=username, role='staff')
    staff.set_password(password)
    db.session.add(staff)
    db.session.commit()

    flash(f'Staff "{username}" added successfully!', 'success')
    return redirect(url_for('dashboard.admin_dashboard'))


@dashboard_bp.route('/admin/delete-staff/<int:staff_id>', methods=['POST'])
@login_required
def delete_staff(staff_id):
    """Admin deletes a staff member."""
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    staff = User.query.get_or_404(staff_id)
    if staff.role != 'staff':
        flash('Cannot delete this user.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    # Unlink students created by this staff so they are preserved
    Student.query.filter_by(created_by=staff.id).update({'created_by': None})
    db.session.delete(staff)
    db.session.commit()
    flash(f'Staff "{staff.username}" deleted.', 'success')
    return redirect(url_for('dashboard.admin_dashboard'))


@dashboard_bp.route('/admin/add-admin', methods=['POST'])
@login_required
def add_admin():
    """Admin adds a new admin account."""
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    current_admin_count = User.query.filter_by(role='admin').count()
    if current_admin_count >= 4:
        flash('Maximum limit of 4 admins reached.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        flash('Username and Password are required.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    if len(password) < 4:
        flash('Password must be at least 4 characters.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    admin = User(username=username, role='admin')
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    flash(f'Admin "{username}" added successfully!', 'success')
    return redirect(url_for('dashboard.admin_dashboard'))


@dashboard_bp.route('/admin/delete-admin/<int:admin_id>', methods=['POST'])
@login_required
def delete_admin(admin_id):
    """Admin deletes another admin account."""
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    admin = User.query.get_or_404(admin_id)
    if admin.role != 'admin':
        flash('Cannot delete this user.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    # Prevent deleting yourself
    if admin.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    db.session.delete(admin)
    db.session.commit()
    flash(f'Admin "{admin.username}" deleted.', 'success')
    return redirect(url_for('dashboard.admin_dashboard'))


# ============================================================
#  MESSAGES PAGE (All Roles)
# ============================================================

@dashboard_bp.route('/messages')
@login_required
def messages_page():
    """Dedicated messages page for all roles."""
    role = session.get('user_role')

    if role == 'admin':
        admin_messages = Message.query.filter(
            ((Message.receiver_type == 'admin') & (Message.receiver_id == current_user.id)) |
            ((Message.sender_type == 'admin') & (Message.sender_id == current_user.id))
        ).filter(Message.parent_id == None).order_by(Message.created_at.desc()).all()

        unread_msg_count = Message.query.filter_by(
            receiver_type='admin', receiver_id=current_user.id, is_read=False
        ).count()

        staff_list = User.query.filter_by(role='staff').order_by(User.created_at.desc()).all()

        return render_template('messages.html',
                               role='admin',
                               messages=admin_messages,
                               unread_msg_count=unread_msg_count,
                               staff_list=staff_list)

    elif role == 'staff':
        student_messages = Message.query.filter(
            ((Message.receiver_type == 'staff') & (Message.receiver_id == current_user.id) & (Message.sender_type == 'student')) |
            ((Message.sender_type == 'staff') & (Message.sender_id == current_user.id) & (Message.receiver_type == 'student'))
        ).filter(Message.parent_id == None).order_by(Message.created_at.desc()).all()

        admin_messages = Message.query.filter(
            ((Message.receiver_type == 'staff') & (Message.receiver_id == current_user.id) & (Message.sender_type == 'admin')) |
            ((Message.sender_type == 'staff') & (Message.sender_id == current_user.id) & (Message.receiver_type == 'admin'))
        ).filter(Message.parent_id == None).order_by(Message.created_at.desc()).all()

        unread_msg_count = Message.query.filter_by(
            receiver_type='staff', receiver_id=current_user.id, is_read=False
        ).count()

        admin_list = User.query.filter_by(role='admin').all()

        students = Student.query.filter_by(created_by=current_user.id).all()
        student_data = []
        for s in students:
            student_data.append({'student': s})

        return render_template('messages.html',
                               role='staff',
                               student_messages=student_messages,
                               admin_messages=admin_messages,
                               unread_msg_count=unread_msg_count,
                               admin_list=admin_list,
                               student_data=student_data)

    elif role == 'student':
        student = current_user
        student_messages = Message.query.filter(
            ((Message.sender_type == 'student') & (Message.sender_id == student.id)) |
            ((Message.receiver_type == 'student') & (Message.receiver_id == student.id))
        ).filter(Message.parent_id == None).order_by(Message.created_at.desc()).all()

        unread_count = Message.query.filter_by(
            receiver_type='student', receiver_id=student.id, is_read=False
        ).count()

        assigned_staff = User.query.get(student.created_by) if student.created_by else None

        return render_template('messages.html',
                               role='student',
                               student=student,
                               messages=student_messages,
                               unread_count=unread_count,
                               assigned_staff=assigned_staff)

    flash('Access denied.', 'error')
    return redirect(url_for('auth.role_select'))


# ============================================================
#  STAFF DASHBOARD
# ============================================================

@dashboard_bp.route('/staff')
@login_required
def staff_dashboard():
    """Staff dashboard — add students, enter marks, predict."""
    if session.get('user_role') != 'staff':
        flash('Access denied. Staff only.', 'error')
        return redirect(url_for('auth.role_select'))

    students = Student.query.filter_by(created_by=current_user.id).order_by(Student.created_at.desc()).all()
    total_students = len(students)

    # Get academic records for each student
    student_data = []
    total_attendance = 0
    attendance_count = 0
    pending_predictions = 0

    for s in students:
        academic = StudentAcademic.query.filter_by(reg_no=s.reg_no).first()
        student_data.append({
            'student': s,
            'academic': academic
        })
        if academic:
            if academic.attendance:
                total_attendance += academic.attendance
                attendance_count += 1
            if not academic.prediction_result:
                pending_predictions += 1
        else:
            pending_predictions += 1

    avg_attendance = round(total_attendance / attendance_count, 1) if attendance_count > 0 else 0

    # Get messages for this staff member (exclude outgoing messages to admins to prevent them from showing in Student Messages inbox)
    # For student messages (staff -> student OR student -> staff)
    student_messages = Message.query.filter(
        ((Message.receiver_type == 'staff') & (Message.receiver_id == current_user.id) & (Message.sender_type == 'student')) |
        ((Message.sender_type == 'staff') & (Message.sender_id == current_user.id) & (Message.receiver_type == 'student'))
    ).filter(Message.parent_id == None).order_by(Message.created_at.desc()).all()

    # For admin messages (staff -> admin OR admin -> staff)
    admin_messages = Message.query.filter(
        ((Message.receiver_type == 'staff') & (Message.receiver_id == current_user.id) & (Message.sender_type == 'admin')) |
        ((Message.sender_type == 'staff') & (Message.sender_id == current_user.id) & (Message.receiver_type == 'admin'))
    ).filter(Message.parent_id == None).order_by(Message.created_at.desc()).all()

    unread_msg_count = Message.query.filter_by(
        receiver_type='staff', receiver_id=current_user.id, is_read=False
    ).count()

    admin_list = User.query.filter_by(role='admin').all()

    return render_template('staff_dashboard.html',
                           student_data=student_data,
                           total_students=total_students,
                           pending_predictions=pending_predictions,
                           avg_attendance=avg_attendance,
                           student_messages=student_messages,
                           admin_messages=admin_messages,
                           unread_msg_count=unread_msg_count,
                           admin_list=admin_list)


@dashboard_bp.route('/staff/add-student', methods=['POST'])
@login_required
def add_student():
    """Staff or Admin adds a new student."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    redirect_to = url_for('dashboard.admin_dashboard') if role == 'admin' else url_for('dashboard.staff_dashboard')

    reg_no = request.form.get('reg_no', '').strip()
    name = request.form.get('name', '').strip()
    dept = request.form.get('dept', '').strip()
    year = request.form.get('year', '1')
    password = request.form.get('password', '')

    if not all([reg_no, name, dept, password]):
        flash('All fields are required.', 'error')
        return redirect(redirect_to)

    if Student.query.filter_by(reg_no=reg_no).first():
        flash('Please enter a valid register number.', 'error')
        return redirect(redirect_to)

    # Determine who the student is assigned to
    if role == 'admin':
        staff_id = request.form.get('staff_id', '')
        if not staff_id:
            flash('Please select a staff member to assign this student.', 'error')
            return redirect(redirect_to)
        staff = User.query.get(int(staff_id))
        if not staff or staff.role != 'staff':
            flash('Invalid staff member selected.', 'error')
            return redirect(redirect_to)
        assigned_to = staff.id
    else:
        assigned_to = current_user.id

    student = Student(
        reg_no=reg_no,
        name=name,
        dept=dept,
        year=int(year),
        created_by=assigned_to
    )
    student.set_password(password)
    db.session.add(student)
    db.session.commit()

    flash(f'Student "{name}" (Reg: {reg_no}) added successfully!', 'success')
    return redirect(redirect_to)


@dashboard_bp.route('/staff/enter-marks/<reg_no>', methods=['GET', 'POST'])
@login_required
def enter_marks(reg_no):
    """Staff or Admin enters/updates academic marks for a student."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    redirect_to = url_for('dashboard.admin_dashboard') if role == 'admin' else url_for('dashboard.staff_dashboard')
    student = Student.query.filter_by(reg_no=reg_no).first_or_404()

    if request.method == 'POST':
        # Get or create academic record
        academic = StudentAcademic.query.filter_by(reg_no=reg_no).first()
        if not academic:
            academic = StudentAcademic(reg_no=reg_no)

        try:
            academic.internal_1 = float(request.form.get('internal_1', 0))
            academic.internal_2 = float(request.form.get('internal_2', 0))
            academic.internal_3 = float(request.form.get('internal_3', 0))
            academic.assignment = float(request.form.get('assignment', 0))
            academic.prev_sem_gpa = float(request.form.get('prev_sem_gpa', 0))
            academic.study_hours_per_day = float(request.form.get('study_hours_per_day', 0))
            academic.attendance = float(request.form.get('attendance', 0))
            academic.extra_activity = request.form.get('extra_activity') == 'yes'
            academic.extra_activity_type = request.form.get('extra_activity_type', '').strip() or None

            db.session.add(academic)
            db.session.commit()
            flash(f'Marks saved for {student.name}!', 'success')
        except ValueError:
            flash('Please enter valid numeric values.', 'error')

        return redirect(redirect_to)

    # GET — load existing marks
    academic = StudentAcademic.query.filter_by(reg_no=reg_no).first()
    return render_template('enter_marks.html', student=student, academic=academic)


@dashboard_bp.route('/staff/predict/<reg_no>', methods=['POST'])
@login_required
def run_prediction(reg_no):
    """Staff or Admin runs prediction for a student."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    redirect_to = url_for('dashboard.admin_dashboard') if role == 'admin' else url_for('dashboard.staff_dashboard')

    academic = StudentAcademic.query.filter_by(reg_no=reg_no).first()
    if not academic:
        flash('No academic records found. Enter marks first.', 'error')
        return redirect(redirect_to)

    # Run prediction
    data = {
        'internal_1': academic.internal_1,
        'internal_2': academic.internal_2,
        'internal_3': academic.internal_3,
        'assignment': academic.assignment,
        'prev_sem_gpa': academic.prev_sem_gpa,
        'study_hours_per_day': academic.study_hours_per_day,
        'extra_activity': academic.extra_activity,
        'attendance': academic.attendance
    }
    result = predict_result(data)

    # Save prediction
    academic.prediction_result = result['prediction_result']
    academic.risk_level = result['risk_level']

    # Save to prediction history
    history = PredictionHistory(
        reg_no=reg_no,
        prediction_result=result['prediction_result'],
        risk_level=result['risk_level'],
        grade=result['grade'],
        internal_avg=result['internal_avg'],
        attendance=academic.attendance
    )
    db.session.add(history)
    db.session.commit()

    student = Student.query.filter_by(reg_no=reg_no).first()
    flash(f'Prediction for {student.name}: {result["prediction_result"]} (Risk: {result["risk_level"]}, Grade: {result["grade"]})', 'success')
    return redirect(redirect_to)


@dashboard_bp.route('/staff/delete-student/<reg_no>', methods=['POST'])
@login_required
def delete_student(reg_no):
    """Staff or Admin deletes a student and their academic records."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    redirect_to = url_for('dashboard.admin_dashboard') if role == 'admin' else url_for('dashboard.staff_dashboard')
    student = Student.query.filter_by(reg_no=reg_no).first_or_404()

    # Delete prediction history first
    PredictionHistory.query.filter_by(reg_no=reg_no).delete()
    # Delete academic records
    StudentAcademic.query.filter_by(reg_no=reg_no).delete()
    db.session.delete(student)
    db.session.commit()

    flash(f'Student "{student.name}" deleted.', 'success')
    return redirect(redirect_to)


# ============================================================
#  EDIT STUDENT  (Admin & Staff)
# ============================================================

@dashboard_bp.route('/edit-student/<reg_no>', methods=['POST'])
@login_required
def edit_student(reg_no):
    """Admin or Staff edits student details."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    redirect_to = url_for('dashboard.admin_dashboard') if role == 'admin' else url_for('dashboard.staff_dashboard')
    student = Student.query.filter_by(reg_no=reg_no).first_or_404()

    new_name = request.form.get('name', '').strip()
    new_dept = request.form.get('dept', '').strip()
    new_year = request.form.get('year', '')
    new_password = request.form.get('password', '').strip()

    if new_name:
        student.name = new_name
    if new_dept:
        student.dept = new_dept
    if new_year:
        student.year = int(new_year)
    if new_password and len(new_password) >= 4:
        student.set_password(new_password)

    db.session.commit()
    flash(f'Student "{student.name}" updated successfully!', 'success')
    return redirect(redirect_to)


# ============================================================
#  BATCH PREDICT  (Staff & Admin)
# ============================================================

@dashboard_bp.route('/batch-predict', methods=['POST'])
@login_required
def batch_predict():
    """Run prediction for all students who have marks but no prediction."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    redirect_to = url_for('dashboard.admin_dashboard') if role == 'admin' else url_for('dashboard.staff_dashboard')

    if role == 'admin':
        academics = StudentAcademic.query.filter(
            (StudentAcademic.prediction_result == None) | (StudentAcademic.prediction_result == '')
        ).all()
    else:
        # Staff only predicts their own students
        student_regnos = [s.reg_no for s in Student.query.filter_by(created_by=current_user.id).all()]
        academics = StudentAcademic.query.filter(
            StudentAcademic.reg_no.in_(student_regnos),
            (StudentAcademic.prediction_result == None) | (StudentAcademic.prediction_result == '')
        ).all()

    count = 0
    for academic in academics:
        data = {
            'internal_1': academic.internal_1,
            'internal_2': academic.internal_2,
            'internal_3': academic.internal_3,
            'assignment': academic.assignment,
            'prev_sem_gpa': academic.prev_sem_gpa,
            'study_hours_per_day': academic.study_hours_per_day,
            'extra_activity': academic.extra_activity,
            'attendance': academic.attendance
        }
        result = predict_result(data)
        academic.prediction_result = result['prediction_result']
        academic.risk_level = result['risk_level']

        # Save to prediction history
        history = PredictionHistory(
            reg_no=academic.reg_no,
            prediction_result=result['prediction_result'],
            risk_level=result['risk_level'],
            grade=result['grade'],
            internal_avg=result['internal_avg'],
            attendance=academic.attendance
        )
        db.session.add(history)
        count += 1

    db.session.commit()
    flash(f'Batch prediction complete! {count} student(s) predicted.', 'success')
    return redirect(redirect_to)


# ============================================================
#  DOWNLOAD CSV
# ============================================================

@dashboard_bp.route('/download-students')
@login_required
def download_students():
    """Staff or Admin downloads student details as CSV."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    if role == 'admin':
        students = Student.query.order_by(Student.name).all()
    else:
        students = Student.query.filter_by(created_by=current_user.id).order_by(Student.name).all()

    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'Reg No', 'Name', 'Department', 'Year',
                     'Internal 1', 'Internal 2', 'Internal 3', 'Assignment',
                     'Internal Avg', 'Prev Sem GPA', 'Study Hours/Day',
                     'Attendance %', 'Extra Activity', 'Result', 'Risk Level'])

    for i, s in enumerate(students, 1):
        academic = StudentAcademic.query.filter_by(reg_no=s.reg_no).first()
        if academic:
            writer.writerow([
                i, s.reg_no, s.name, s.dept, s.year,
                academic.internal_1, academic.internal_2, academic.internal_3,
                academic.assignment, academic.internal_avg(),
                academic.prev_sem_gpa, academic.study_hours_per_day,
                'Yes' if academic.extra_activity else 'No',
                academic.prediction_result or 'Pending',
                academic.risk_level or '-'
            ])
        else:
            writer.writerow([
                i, s.reg_no, s.name, s.dept, s.year,
                '-', '-', '-', '-', '-', '-', '-', '-', '-', 'Pending', '-'
            ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=student_details.csv'
    return response


@dashboard_bp.route('/download-students/<risk_level>')
@login_required
def download_students_by_risk(risk_level):
    """Staff or Admin downloads student details filtered by risk level as CSV."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    # Validate risk level
    if risk_level not in ('Low', 'Medium', 'High'):
        flash('Invalid risk level.', 'error')
        redirect_to = url_for('dashboard.admin_dashboard') if role == 'admin' else url_for('dashboard.staff_dashboard')
        return redirect(redirect_to)

    if role == 'admin':
        students = Student.query.order_by(Student.name).all()
    else:
        students = Student.query.filter_by(created_by=current_user.id).order_by(Student.name).all()

    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'Reg No', 'Name', 'Department', 'Year',
                     'Internal 1', 'Internal 2', 'Internal 3', 'Assignment',
                     'Internal Avg', 'Prev Sem GPA', 'Study Hours/Day',
                     'Attendance %', 'Extra Activity', 'Result', 'Risk Level'])

    count = 0
    for s in students:
        academic = StudentAcademic.query.filter_by(reg_no=s.reg_no).first()
        if academic and academic.risk_level == risk_level:
            count += 1
            writer.writerow([
                count, s.reg_no, s.name, s.dept, s.year,
                academic.internal_1, academic.internal_2, academic.internal_3,
                academic.assignment, academic.internal_avg(),
                academic.prev_sem_gpa, academic.study_hours_per_day,
                academic.attendance,
                'Yes' if academic.extra_activity else 'No',
                academic.prediction_result or 'Pending',
                academic.risk_level or '-'
            ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={risk_level.lower()}_risk_students.csv'
    return response


# ============================================================
#  BULK CSV UPLOAD
# ============================================================

@dashboard_bp.route('/download-csv-template')
@login_required
def download_csv_template():
    """Download the empty CSV template for bulk importing."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Reg No', 'Name', 'Dept', 'Year', 'Password', 'Internal 1', 'Internal 2', 'Internal 3', 'Prev Sem CGPA', 'Assignment', 'Attendance', 'Extra Activities', 'Study Hours'])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=Bulk_Student_Template.csv'
    return response


@dashboard_bp.route('/upload-students-csv', methods=['POST'])
@login_required
def upload_students_csv():
    """Process a CSV to bulk add students and academic marks."""
    role = session.get('user_role')
    if role not in ('staff', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    redirect_to = url_for('dashboard.admin_dashboard') if role == 'admin' else url_for('dashboard.staff_dashboard')

    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(redirect_to)
        
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(redirect_to)

    if not file.filename.endswith('.csv'):
        flash('File must be a CSV format.', 'error')
        return redirect(redirect_to)

    # Determine assigned staff
    if role == 'admin':
        staff_id = request.form.get('staff_id', '')
        if not staff_id:
            flash('Please select a staff member to assign these students.', 'error')
            return redirect(redirect_to)
        staff = User.query.get(int(staff_id))
        if not staff or staff.role != 'staff':
            flash('Invalid staff member selected.', 'error')
            return redirect(redirect_to)
        assigned_to = staff.id
    else:
        assigned_to = current_user.id

    import csv
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    
    # Skip header
    try:
        next(csv_input)
    except StopIteration:
        flash('Empty CSV file.', 'error')
        return redirect(redirect_to)

    success_count = 0
    skip_count = 0
    error_count = 0
    
    for row in csv_input:
        if not row or not row[0].strip():
            continue # Skip empty rows
            
        try:
            # Basic validation
            # Current template: Reg No, Name, Dept, Year, Password, In1, In2, In3, CGPA, Assign, Atten, Extra, Study
            if len(row) < 5:
                error_count += 1
                continue
                
            reg_no = row[0].strip()
            name = row[1].strip()
            dept = row[2].strip()
            year_str = row[3].strip()
            password = row[4].strip()
            
            if not all([reg_no, name, dept, year_str, password]):
                error_count += 1
                continue
                
            year = int(year_str) if year_str.isdigit() else 1
            
            # Check for existing student
            if Student.query.filter_by(reg_no=reg_no).first():
                skip_count += 1
                continue
                
            # Create student
            student = Student(
                reg_no=reg_no,
                name=name,
                dept=dept,
                year=year,
                created_by=assigned_to
            )
            student.set_password(password)
            db.session.add(student)
            
            # Parse academics if available
            if len(row) >= 13:
                # Helper function for safe float parsing
                def parse_float(val, default=0.0):
                    try: return float(val.strip())
                    except: return default
                
                academic = StudentAcademic(
                    reg_no=reg_no,
                    internal_1=parse_float(row[5]),
                    internal_2=parse_float(row[6]),
                    internal_3=parse_float(row[7]),
                    prev_sem_gpa=parse_float(row[8]),
                    assignment=parse_float(row[9]),
                    attendance=parse_float(row[10]),
                    extra_activity=(row[11].strip().lower() in ['yes', 'y', '1', 'true']),
                    study_hours_per_day=parse_float(row[12])
                )
                db.session.add(academic)

            success_count += 1
        except Exception as e:
            error_count += 1
            
    try:
        db.session.commit()
        if success_count > 0:
            flash(f'Successfully imported {success_count} student(s) with marks! (Skipped: {skip_count}, Errors: {error_count})', 'success')
        else:
            flash(f'No students imported. (Skipped: {skip_count}, Errors: {error_count})', 'error')
    except Exception as e:
        db.session.rollback()
        flash('Database error occurred during import.', 'error')

    return redirect(redirect_to)


# ============================================================
#  STUDENT DASHBOARD
# ============================================================

@dashboard_bp.route('/student')
@login_required
def student_dashboard():
    """Student dashboard — view own details + prediction."""
    if session.get('user_role') != 'student':
        flash('Access denied. Student only.', 'error')
        return redirect(url_for('auth.role_select'))

    student = current_user
    academic = StudentAcademic.query.filter_by(reg_no=student.reg_no).first()

    # Get prediction suggestions if academic data exists
    suggestions = []
    prediction = None
    if academic and academic.prediction_result:
        data = {
            'internal_1': academic.internal_1,
            'internal_2': academic.internal_2,
            'internal_3': academic.internal_3,
            'assignment': academic.assignment,
            'prev_sem_gpa': academic.prev_sem_gpa,
            'study_hours_per_day': academic.study_hours_per_day,
            'extra_activity': academic.extra_activity,
            'attendance': academic.attendance
        }
        prediction = predict_result(data)
        suggestions = prediction.get('suggestions', [])

    # Get prediction history
    prediction_history = PredictionHistory.query.filter_by(
        reg_no=student.reg_no
    ).order_by(PredictionHistory.created_at.desc()).all()

    # Calculate performance score (0-100) for gauge
    performance_score = 0
    if academic:
        internal_avg = academic.internal_avg()
        score = 0
        score += (internal_avg / 100) * 35  # 35% weight for internal avg
        score += (academic.prev_sem_gpa / 10) * 25  # 25% weight for GPA
        score += (academic.attendance / 100) * 20  # 20% weight for attendance
        score += (min(academic.study_hours_per_day, 6) / 6) * 10  # 10% weight for study hours
        score += (academic.assignment / 30) * 10  # 10% weight for assignment
        performance_score = round(min(score, 100), 1)

    # Calculate department average performance score for comparison gauge
    dept_avg_score = 0
    if academic:
        dept_students = Student.query.filter_by(dept=student.dept).all()
        dept_reg_nos = [s.reg_no for s in dept_students]
        dept_academics = StudentAcademic.query.filter(
            StudentAcademic.reg_no.in_(dept_reg_nos)
        ).all()
        if dept_academics:
            total_dept_score = 0
            for da in dept_academics:
                ds = 0
                ds += (da.internal_avg() / 100) * 35
                ds += (da.prev_sem_gpa / 10) * 25
                ds += (da.attendance / 100) * 20
                ds += (min(da.study_hours_per_day, 6) / 6) * 10
                ds += (da.assignment / 30) * 10
                total_dept_score += min(ds, 100)
            dept_avg_score = round(total_dept_score / len(dept_academics), 1)

    # Get messages for this student
    student_messages = Message.query.filter(
        ((Message.sender_type == 'student') & (Message.sender_id == student.id)) |
        ((Message.receiver_type == 'student') & (Message.receiver_id == student.id))
    ).filter(Message.parent_id == None).order_by(Message.created_at.desc()).all()

    # Get unread count
    unread_count = Message.query.filter_by(
        receiver_type='student', receiver_id=student.id, is_read=False
    ).count()

    # Get assigned staff name
    assigned_staff = User.query.get(student.created_by) if student.created_by else None

    return render_template('student_dashboard.html',
                           student=student,
                           academic=academic,
                           prediction=prediction,
                           suggestions=suggestions,
                           prediction_history=prediction_history,
                           performance_score=performance_score,
                           dept_avg_score=dept_avg_score,
                           messages=student_messages,
                           unread_count=unread_count,
                           assigned_staff=assigned_staff)


@dashboard_bp.route('/student/change-password', methods=['POST'])
@login_required
def change_password():
    """Student changes their own password."""
    if session.get('user_role') != 'student':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_pw or not new_pw or not confirm_pw:
        flash('All password fields are required.', 'error')
        return redirect(url_for('dashboard.student_dashboard'))

    if not current_user.check_password(current_pw):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('dashboard.student_dashboard'))

    if len(new_pw) < 4:
        flash('New password must be at least 4 characters.', 'error')
        return redirect(url_for('dashboard.student_dashboard'))

    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('dashboard.student_dashboard'))

    current_user.set_password(new_pw)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('dashboard.student_dashboard'))


@dashboard_bp.route('/student/download-report')
@login_required
def download_prediction():
    """Student downloads their prediction result as an Enhanced PDF."""
    if session.get('user_role') != 'student':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    student = current_user
    academic = StudentAcademic.query.filter_by(reg_no=student.reg_no).first()

    if not academic or not academic.prediction_result:
        flash('No prediction result available to download.', 'error')
        return redirect(url_for('dashboard.student_dashboard'))

    # Run prediction to get full results (suggestions, etc.)
    data = {
        'internal_1': academic.internal_1,
        'internal_2': academic.internal_2,
        'internal_3': academic.internal_3,
        'assignment': academic.assignment,
        'prev_sem_gpa': academic.prev_sem_gpa,
        'study_hours_per_day': academic.study_hours_per_day,
        'extra_activity': academic.extra_activity,
        'attendance': academic.attendance
    }
    prediction = predict_result(data)

    import io
    from datetime import datetime
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=12*mm, bottomMargin=12*mm,
                            leftMargin=20*mm, rightMargin=20*mm)

    styles = getSampleStyleSheet()

    # Premium Styles
    title_style = ParagraphStyle('PremiumTitle', parent=styles['Title'],
                                 fontSize=22, textColor=colors.HexColor('#0F172A'),
                                 alignment=TA_LEFT, fontName='Helvetica-Bold', spaceAfter=2)
    subtitle_style = ParagraphStyle('PremiumSubtitle', parent=styles['Normal'],
                                    fontSize=11, textColor=colors.HexColor('#64748B'),
                                    alignment=TA_LEFT, fontName='Helvetica', spaceAfter=15)
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'],
                                     fontSize=14, textColor=colors.HexColor('#1E293B'),
                                     fontName='Helvetica-Bold', spaceBefore=18, spaceAfter=8)
    suggestion_text = ParagraphStyle('SuggestionText', parent=styles['Normal'],
                                     fontSize=10, textColor=colors.HexColor('#334155'), 
                                     leading=16, spaceAfter=6, leftIndent=15, bulletIndent=5)

    elements = []

    # Header Section
    elements.append(Paragraph("ACADEMIC PERFORMANCE REPORT", title_style))
    elements.append(Paragraph(f"Generated for {student.name.upper()} | Register No: {student.reg_no}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3B82F6'), spaceAfter=8))

    # Student Profile Table
    info_data = [
        ['STUDENT PROFILE', ''],
        ['Name:', student.name, 'Department:', student.dept.upper()],
        ['Register No:', student.reg_no, 'Year:', f"Year {student.year}"]
    ]
    info_table = Table(info_data, colWidths=[80, 160, 80, 160])
    info_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (3, 0)),
        ('BACKGROUND', (0, 0), (3, 0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (3, 0), colors.HexColor('#0F172A')),
        ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (3, 0), 11),
        ('BOTTOMPADDING', (0, 0), (3, 0), 8),
        ('TOPPADDING', (0, 0), (3, 0), 8),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1E293B')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # Performance Chart Analysis
    elements.append(Paragraph("Performance Analysis", section_heading))
    
    try:
        drawing = Drawing(400, 130)
        bc = VerticalBarChart()
        bc.x = 20
        bc.y = 20
        bc.height = 100
        bc.width = 440
        bc.data = [[academic.internal_1, academic.internal_2, academic.internal_3]]
        bc.strokeColor = colors.HexColor('#FFFFFF')
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.valueAxis.labels.fontSize = 8
        bc.valueAxis.labels.fontName = 'Helvetica'
        bc.categoryAxis.labels.fontSize = 9
        bc.categoryAxis.labels.fontName = 'Helvetica'
        bc.categoryAxis.labels.dy = -10
        bc.categoryAxis.categoryNames = ['Internal 1', 'Internal 2', 'Internal 3']
        bc.bars[0].fillColor = colors.HexColor('#3B82F6')
        bc.barSpacing = 30
        drawing.add(bc)
        elements.append(drawing)
    except Exception as e:
        print("Could not generate chart:", e)

    elements.append(Spacer(1, 10))

    # Detailed Marks Table
    marks_data = [
        ['Metric', 'Score / Value', 'Metric', 'Score / Value'],
        ['Internal 1', f"{academic.internal_1:.1f} / 100", 'Internal 2', f"{academic.internal_2:.1f} / 100"],
        ['Internal 3', f"{academic.internal_3:.1f} / 100", 'Assignment', f"{academic.assignment:.1f} / 30"],
        ['Internal Average', f"{academic.internal_avg():.1f} / 100", 'Prev Sem GPA', f"{academic.prev_sem_gpa:.2f} / 10"],
        ['Attendance %', f"{academic.attendance:.1f}%", 'Study Hours', f"{academic.study_hours_per_day:.1f} hrs"],
    ]
    marks_table = Table(marks_data, colWidths=[120, 120, 120, 120])
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
    ]))
    elements.append(marks_table)
    elements.append(Spacer(1, 12))

    # Prediction Outcome
    elements.append(Paragraph("Prediction Outcome", section_heading))
    
    res = str(prediction.get('prediction_result', 'N/A')).title()
    risk = str(prediction.get('risk_level', 'N/A')).title()
    grade = str(prediction.get('grade', 'N/A')).upper()
    
    res_color = colors.HexColor('#16A34A') if res.lower() == 'pass' else colors.HexColor('#DC2626')
    risk_color = colors.HexColor('#16A34A') if risk.lower() == 'low' else (colors.HexColor('#EA580C') if risk.lower() == 'medium' else colors.HexColor('#DC2626'))

    outcome_data = [
        ['Overall Prediction', 'Estimated Grade', 'Risk Level'],
        [res.upper(), grade, risk.upper()]
    ]
    outcome_table = Table(outcome_data, colWidths=[160, 160, 160])
    outcome_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 16),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TEXTCOLOR', (0, 1), (0, 1), res_color),
        ('TEXTCOLOR', (2, 1), (2, 1), risk_color),
    ]))
    elements.append(outcome_table)
    elements.append(Spacer(1, 15))

    # Suggestions for Improvement
    suggestions = prediction.get('suggestions', [])
    if suggestions:
        elements.append(Paragraph("Diagnostic Suggestions", section_heading))
        for suggestion in suggestions:
            elements.append(Paragraph(f"• {suggestion}", suggestion_text))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#94A3B8'), alignment=TA_CENTER)
    elements.append(Paragraph(f"Report generated automatically on {datetime.now().strftime('%d %b %Y, %I:%M %p')}", footer_style))
    elements.append(Paragraph("Academic Performance Prediction System — Confidential", footer_style))

    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Prediction_Report_{student.reg_no}.pdf'
    return response


# ============================================================
#  MESSAGING SYSTEM (Ask Staff)
@dashboard_bp.route('/student/send-message', methods=['POST'])
@login_required
def send_message():
    """Student sends a message to their assigned staff."""
    if session.get('user_role') != 'student':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    student = current_user
    subject = request.form.get('subject', '').strip()
    content = request.form.get('content', '').strip()

    if not subject or not content:
        flash('Subject and message are required.', 'error')
        return redirect(url_for('dashboard.student_dashboard'))

    if not student.created_by:
        flash('No staff assigned. Please contact admin.', 'error')
        return redirect(url_for('dashboard.student_dashboard'))

    msg = Message(
        sender_type='student',
        sender_id=student.id,
        receiver_type='staff',
        receiver_id=student.created_by,
        subject=subject,
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    flash('Message sent to your staff!', 'success')
    return redirect(url_for('dashboard.messages_page'))


@dashboard_bp.route('/student/mark-read/<int:msg_id>', methods=['POST'])
@login_required
def mark_message_read(msg_id):
    """Student marks a message/reply as read."""
    if session.get('user_role') != 'student':
        return redirect(url_for('auth.role_select'))

    msg = Message.query.get_or_404(msg_id)
    if msg.receiver_type == 'student' and msg.receiver_id == current_user.id:
        msg.is_read = True
        db.session.commit()
    return redirect(url_for('dashboard.messages_page'))


@dashboard_bp.route('/student/reply-message/<int:msg_id>', methods=['POST'])
@login_required
def student_reply_message(msg_id):
    """Student replies to a message thread."""
    if session.get('user_role') != 'student':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    parent_msg = Message.query.get_or_404(msg_id)
    content = request.form.get('content', '').strip()

    if not content:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('dashboard.messages_page'))

    reply = Message(
        sender_type='student',
        sender_id=current_user.id,
        receiver_type='staff',
        receiver_id=parent_msg.receiver_id,
        subject=f'Re: {parent_msg.subject}',
        content=content,
        parent_id=parent_msg.id
    )

    for rep in parent_msg.replies:
        if rep.receiver_type == 'student' and rep.receiver_id == current_user.id and not rep.is_read:
            rep.is_read = True

    db.session.add(reply)
    db.session.commit()
    flash('Reply sent successfully.', 'success')
    return redirect(url_for('dashboard.messages_page'))


@dashboard_bp.route('/staff/reply-message/<int:msg_id>', methods=['POST'])
@login_required
def reply_message(msg_id):
    """Staff replies to a student message."""
    if session.get('user_role') != 'staff':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    parent_msg = Message.query.get_or_404(msg_id)
    content = request.form.get('content', '').strip()

    if not content:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('dashboard.messages_page'))

    reply = Message(
        sender_type='staff',
        sender_id=current_user.id,
        receiver_type='student',
        receiver_id=parent_msg.sender_id,
        subject=f'Re: {parent_msg.subject}',
        content=content,
        parent_id=parent_msg.id
    )
    # Mark original as read
    parent_msg.is_read = True
    db.session.add(reply)
    db.session.commit()

    flash('Reply sent!', 'success')
    return redirect(url_for('dashboard.messages_page'))


@dashboard_bp.route('/staff/mark-read/<int:msg_id>', methods=['POST'])
@login_required
def mark_staff_message_read(msg_id):
    """Staff marks a message as read without replying."""
    if session.get('user_role') != 'staff':
        return redirect(url_for('auth.role_select'))

    msg = Message.query.get_or_404(msg_id)
    if msg.receiver_type == 'staff' and msg.receiver_id == current_user.id:
        msg.is_read = True
        db.session.commit()
    return redirect(url_for('dashboard.messages_page'))


@dashboard_bp.route('/admin/mark-read/<int:msg_id>', methods=['POST'])
@login_required
def mark_admin_message_read(msg_id):
    """Admin marks a message as read."""
    if session.get('user_role') != 'admin':
        return redirect(url_for('auth.role_select'))

    msg = Message.query.get_or_404(msg_id)
    if msg.receiver_type == 'admin':
        msg.is_read = True
        db.session.commit()
    return redirect(url_for('dashboard.messages_page'))


@dashboard_bp.route('/admin/reply-message/<int:msg_id>', methods=['POST'])
@login_required
def admin_reply_message(msg_id):
    """Admin replies to a staff message."""
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    parent_msg = Message.query.get_or_404(msg_id)
    content = request.form.get('content', '').strip()

    if not content:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('dashboard.messages_page'))

    reply = Message(
        sender_type='admin',
        sender_id=current_user.id,
        receiver_type='staff',
        receiver_id=parent_msg.sender_id,
        subject=f'Re: {parent_msg.subject}',
        content=content,
        parent_id=parent_msg.id
    )
    # Mark original as read
    parent_msg.is_read = True
    db.session.add(reply)
    db.session.commit()

    flash('Reply sent!', 'success')
    return redirect(url_for('dashboard.messages_page'))


@dashboard_bp.route('/staff/send-admin', methods=['POST'])
@login_required
def staff_send_admin_message():
    """Staff sends a message to an Admin."""
    if session.get('user_role') != 'staff':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    admin_id = request.form.get('admin_id')
    subject = request.form.get('subject', '').strip()
    content = request.form.get('content', '').strip()

    if not admin_id or not subject or not content:
        flash('Admin selection, subject, and message are required.', 'error')
        return redirect(url_for('dashboard.staff_dashboard'))

    msg = Message(
        sender_type='staff',
        sender_id=current_user.id,
        receiver_type='admin',
        receiver_id=int(admin_id),
        subject=subject,
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    flash('Message sent to Admin!', 'success')
    return redirect(url_for('dashboard.messages_page'))


@dashboard_bp.route('/admin/send-staff', methods=['POST'])
@login_required
def admin_send_staff_message():
    """Admin sends a message to a Staff member."""
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('auth.role_select'))

    staff_id = request.form.get('staff_id')
    subject = request.form.get('subject', '').strip()
    content = request.form.get('content', '').strip()

    if not staff_id or not subject or not content:
        flash('Staff selection, subject, and message are required.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

    msg = Message(
        sender_type='admin',
        sender_id=current_user.id,
        receiver_type='staff',
        receiver_id=int(staff_id),
        subject=subject,
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    flash('Message sent to Staff!', 'success')
    return redirect(url_for('dashboard.messages_page'))



@dashboard_bp.route('/message/delete/<int:msg_id>', methods=['POST'])
@login_required
def delete_message(msg_id):
    """Delete a message and its replies if it is a parent."""
    message = Message.query.get_or_404(msg_id)
    
    role = session.get('user_role')
    user_id = current_user.id
    
    if message.parent_id is None:
        if not ((message.sender_type == role and message.sender_id == user_id) or 
                (message.receiver_type == role and message.receiver_id == user_id)):
            flash('Unauthorized to delete this message.', 'error')
            return redirect(url_for('dashboard.messages_page'))
        
        # Delete all replies first
        Message.query.filter_by(parent_id=msg_id).delete()
    else:
        parent = Message.query.get(message.parent_id)
        if parent and not ((parent.sender_type == role and parent.sender_id == user_id) or 
                           (parent.receiver_type == role and parent.receiver_id == user_id)):
            flash('Unauthorized to delete this reply.', 'error')
            return redirect(url_for('dashboard.messages_page'))

    db.session.delete(message)
    db.session.commit()
    
    flash('Message deleted.', 'success')
    return redirect(url_for('dashboard.messages_page'))
