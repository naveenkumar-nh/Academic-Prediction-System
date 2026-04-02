"""
Rule-Based Academic Performance Prediction

Rules:
- If internal_avg < 40 OR prev_sem_gpa < 5 OR study_hours < 1 → High Risk, Fail
- If internal_avg 40-59 AND study_hours 1-2 → Medium Risk, Pass
- If internal_avg >= 60 AND prev_sem_gpa >= 6 AND study_hours >= 2 → Low Risk, Pass
- If extra_activity = Yes and marks are good → bonus level upgrade
"""


def predict_result(data):
    """
    Predict academic result using rule-based logic.

    Args:
        data: dict with keys: internal_1, internal_2, internal_3, assignment,
              prev_sem_gpa, study_hours_per_day, extra_activity

    Returns:
        dict with prediction_result (Pass/Fail), risk_level (Low/Medium/High),
        grade (A/B/C/D/F), attendance, and suggestions list
    """
    internal_avg = (data['internal_1'] + data['internal_2'] + data['internal_3']) / 3
    prev_sem_gpa = data['prev_sem_gpa']
    study_hours = data['study_hours_per_day']
    assignment = data['assignment']
    extra_activity = data.get('extra_activity', False)
    attendance = data.get('attendance', 0)

    # Determine risk level and result
    if internal_avg < 40 or prev_sem_gpa < 5 or study_hours < 1 or attendance < 50:
        risk_level = 'High'
        prediction_result = 'Fail'
    elif 40 <= internal_avg < 60 and 1 <= study_hours <= 2:
        risk_level = 'Medium'
        prediction_result = 'Pass'
    elif internal_avg >= 60 and prev_sem_gpa >= 6 and study_hours >= 2:
        risk_level = 'Low'
        prediction_result = 'Pass'
    else:
        # Default cases
        if internal_avg >= 50 and prev_sem_gpa >= 5:
            risk_level = 'Medium'
            prediction_result = 'Pass'
        else:
            risk_level = 'High'
            prediction_result = 'Fail'

    # Bonus for extra activities (upgrade risk level if passing)
    if extra_activity and prediction_result == 'Pass':
        if risk_level == 'High':
            risk_level = 'Medium'
        elif risk_level == 'Medium':
            risk_level = 'Low'

    # Attendance penalty (if below 75%, increase risk)
    if attendance < 75 and prediction_result == 'Pass':
        if risk_level == 'Low':
            risk_level = 'Medium'
        elif risk_level == 'Medium':
            risk_level = 'High'

    # Grade calculation based on internal average
    if internal_avg >= 90:
        grade = 'A+'
    elif internal_avg >= 80:
        grade = 'A'
    elif internal_avg >= 70:
        grade = 'B'
    elif internal_avg >= 60:
        grade = 'C'
    elif internal_avg >= 50:
        grade = 'D'
    else:
        grade = 'F'

    # Generate suggestions
    suggestions = []
    if internal_avg < 40:
        suggestions.append('Focus on improving internal test scores. Consider extra tutoring.')
    elif internal_avg < 60:
        suggestions.append('Your internal marks are average. Aim for consistent performance.')

    if prev_sem_gpa < 5:
        suggestions.append('Previous semester GPA is low. Review past subjects thoroughly.')
    elif prev_sem_gpa < 6:
        suggestions.append('Try to improve your GPA above 6.0 for better standing.')

    if study_hours < 1:
        suggestions.append('Increase daily study hours to at least 2 hours.')
    elif study_hours < 2:
        suggestions.append('Try to study at least 2-3 hours per day for best results.')

    if assignment < 15:
        suggestions.append('Improve assignment completion and quality.')

    if not extra_activity:
        suggestions.append('Consider participating in extra-curricular activities for holistic development.')

    if attendance < 50:
        suggestions.append('Attendance is critically low. Attend classes regularly to avoid failing.')
    elif attendance < 75:
        suggestions.append('Attendance is below 75%. Improve attendance to maintain eligibility.')
    elif attendance < 85:
        suggestions.append('Try to maintain attendance above 85% for better performance.')

    if not suggestions:
        suggestions.append('Great performance! Keep up the excellent work!')

    return {
        'prediction_result': prediction_result,
        'risk_level': risk_level,
        'grade': grade,
        'internal_avg': round(internal_avg, 2),
        'attendance': attendance,
        'suggestions': suggestions
    }
