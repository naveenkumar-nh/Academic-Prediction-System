"""
REST API Blueprint — JSON endpoints for the Academic Prediction System.
Prefix: /api/v1
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from models.database import db, User, Student, StudentAcademic, PredictionHistory
from models.ml_model import predict_result

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


@api_bp.route('/students', methods=['GET'])
@login_required
def list_students():
    """List all students with optional search, filter, and pagination."""
    search = request.args.get('search', '').strip()
    dept = request.args.get('dept', '').strip()
    risk = request.args.get('risk', '').strip()
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Student.query

    # Search by name, reg_no, or department
    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                Student.name.ilike(like),
                Student.reg_no.ilike(like),
                Student.dept.ilike(like)
            )
        )

    # Filter by department
    if dept:
        query = query.filter(Student.dept == dept)

    # Order by creation date
    query = query.order_by(Student.created_at.desc())

    # Paginate
    per_page = min(per_page, 100)  # cap at 100
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    students = pagination.items

    # Build response with academic data
    results = []
    for s in students:
        academic = StudentAcademic.query.filter_by(reg_no=s.reg_no).first()

        # Apply risk and status filters (post-query since they're in a different table)
        if risk and (not academic or academic.risk_level != risk):
            continue
        if status:
            if status == 'Pending' and academic and academic.prediction_result:
                continue
            elif status != 'Pending' and (not academic or academic.prediction_result != status):
                continue

        student_dict = {
            'id': s.id,
            'reg_no': s.reg_no,
            'name': s.name,
            'dept': s.dept,
            'year': s.year,
            'created_at': s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else None
        }

        if academic:
            student_dict['academic'] = academic.to_dict()
        else:
            student_dict['academic'] = None

        results.append(student_dict)

    return jsonify({
        'success': True,
        'data': results,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@api_bp.route('/students/<reg_no>', methods=['GET'])
@login_required
def get_student(reg_no):
    """Get detailed student information including academic data."""
    student = Student.query.filter_by(reg_no=reg_no).first()
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404

    academic = StudentAcademic.query.filter_by(reg_no=reg_no).first()
    history = PredictionHistory.query.filter_by(
        reg_no=reg_no
    ).order_by(PredictionHistory.created_at.desc()).all()

    result = {
        'id': student.id,
        'reg_no': student.reg_no,
        'name': student.name,
        'dept': student.dept,
        'year': student.year,
        'created_at': student.created_at.strftime('%Y-%m-%d %H:%M') if student.created_at else None,
        'academic': academic.to_dict() if academic else None,
        'prediction_history': [{
            'prediction_result': h.prediction_result,
            'risk_level': h.risk_level,
            'grade': h.grade,
            'internal_avg': h.internal_avg,
            'attendance': h.attendance,
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M') if h.created_at else None
        } for h in history]
    }

    return jsonify({'success': True, 'data': result})


@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get dashboard-level statistics."""
    total_students = Student.query.count()
    total_staff = User.query.filter_by(role='staff').count()
    total_admins = User.query.filter_by(role='admin').count()

    academics = StudentAcademic.query.all()
    total_pass = sum(1 for a in academics if a.prediction_result == 'Pass')
    total_fail = sum(1 for a in academics if a.prediction_result == 'Fail')
    total_pending = total_students - total_pass - total_fail
    total_high_risk = sum(1 for a in academics if a.risk_level == 'High')
    total_medium_risk = sum(1 for a in academics if a.risk_level == 'Medium')
    total_low_risk = sum(1 for a in academics if a.risk_level == 'Low')

    # Department-wise stats
    dept_stats = {}
    students = Student.query.all()
    for s in students:
        if s.dept not in dept_stats:
            dept_stats[s.dept] = {'total': 0, 'pass': 0, 'fail': 0, 'pending': 0}
        dept_stats[s.dept]['total'] += 1
        academic = StudentAcademic.query.filter_by(reg_no=s.reg_no).first()
        if academic and academic.prediction_result == 'Pass':
            dept_stats[s.dept]['pass'] += 1
        elif academic and academic.prediction_result == 'Fail':
            dept_stats[s.dept]['fail'] += 1
        else:
            dept_stats[s.dept]['pending'] += 1

    return jsonify({
        'success': True,
        'data': {
            'total_students': total_students,
            'total_staff': total_staff,
            'total_admins': total_admins,
            'total_pass': total_pass,
            'total_fail': total_fail,
            'total_pending': total_pending,
            'risk': {
                'high': total_high_risk,
                'medium': total_medium_risk,
                'low': total_low_risk
            },
            'department_stats': dept_stats
        }
    })


@api_bp.route('/predict/<reg_no>', methods=['POST'])
@login_required
def api_predict(reg_no):
    """Run prediction for a student and return JSON result."""
    academic = StudentAcademic.query.filter_by(reg_no=reg_no).first()
    if not academic:
        return jsonify({'success': False, 'error': 'No academic records found. Enter marks first.'}), 400

    student = Student.query.filter_by(reg_no=reg_no).first()
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404

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

    return jsonify({
        'success': True,
        'data': {
            'student_name': student.name,
            'reg_no': reg_no,
            'prediction_result': result['prediction_result'],
            'risk_level': result['risk_level'],
            'grade': result['grade'],
            'internal_avg': result['internal_avg'],
            'attendance': result['attendance'],
            'suggestions': result['suggestions']
        }
    })
