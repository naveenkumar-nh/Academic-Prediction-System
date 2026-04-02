"""
Unit tests for the rule-based ML prediction model.
Tests: predict_result() function covering all risk levels, grades, and edge cases.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.ml_model import predict_result


class TestHighRiskFail:
    """Tests for high-risk fail scenarios."""

    def test_low_internal_marks_causes_fail(self):
        """Internal avg < 40 should result in Fail."""
        data = {
            'internal_1': 30, 'internal_2': 25, 'internal_3': 35,
            'assignment': 20, 'prev_sem_gpa': 7.0,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 80
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Fail'
        assert result['risk_level'] == 'High'

    def test_low_gpa_causes_fail(self):
        """Previous semester GPA < 5 should result in Fail."""
        data = {
            'internal_1': 60, 'internal_2': 65, 'internal_3': 70,
            'assignment': 25, 'prev_sem_gpa': 4.0,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 80
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Fail'
        assert result['risk_level'] == 'High'

    def test_low_study_hours_causes_fail(self):
        """Study hours < 1 should result in Fail."""
        data = {
            'internal_1': 60, 'internal_2': 65, 'internal_3': 70,
            'assignment': 25, 'prev_sem_gpa': 7.0,
            'study_hours_per_day': 0.5, 'extra_activity': False, 'attendance': 80
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Fail'
        assert result['risk_level'] == 'High'

    def test_low_attendance_causes_fail(self):
        """Attendance < 50 should result in Fail."""
        data = {
            'internal_1': 70, 'internal_2': 75, 'internal_3': 80,
            'assignment': 25, 'prev_sem_gpa': 7.0,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 40
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Fail'
        assert result['risk_level'] == 'High'


class TestMediumRiskPass:
    """Tests for medium-risk pass scenarios."""

    def test_average_marks_medium_risk(self):
        """Internal avg 40-59 with study hours 1-2 should be Medium risk, Pass."""
        data = {
            'internal_1': 50, 'internal_2': 55, 'internal_3': 45,
            'assignment': 20, 'prev_sem_gpa': 6.0,
            'study_hours_per_day': 1.5, 'extra_activity': False, 'attendance': 80
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Pass'
        assert result['risk_level'] == 'Medium'

    def test_borderline_marks_default_medium(self):
        """Internal avg >= 50 and GPA >= 5 should default to Medium risk, Pass."""
        data = {
            'internal_1': 55, 'internal_2': 55, 'internal_3': 55,
            'assignment': 20, 'prev_sem_gpa': 5.5,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 80
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Pass'


class TestLowRiskPass:
    """Tests for low-risk pass scenarios."""

    def test_good_student_low_risk(self):
        """High marks, good GPA, good study hours should be Low risk, Pass."""
        data = {
            'internal_1': 85, 'internal_2': 90, 'internal_3': 80,
            'assignment': 28, 'prev_sem_gpa': 8.5,
            'study_hours_per_day': 4, 'extra_activity': True, 'attendance': 92
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Pass'
        assert result['risk_level'] == 'Low'


class TestGradeCalculation:
    """Tests for grade assignment."""

    def test_grade_a_plus(self):
        """Internal avg >= 90 should get A+."""
        data = {
            'internal_1': 95, 'internal_2': 92, 'internal_3': 90,
            'assignment': 28, 'prev_sem_gpa': 9.0,
            'study_hours_per_day': 5, 'extra_activity': True, 'attendance': 95
        }
        result = predict_result(data)
        assert result['grade'] == 'A+'

    def test_grade_a(self):
        """Internal avg 80-89 should get A."""
        data = {
            'internal_1': 85, 'internal_2': 82, 'internal_3': 80,
            'assignment': 25, 'prev_sem_gpa': 8.0,
            'study_hours_per_day': 4, 'extra_activity': False, 'attendance': 88
        }
        result = predict_result(data)
        assert result['grade'] == 'A'

    def test_grade_b(self):
        """Internal avg 70-79 should get B."""
        data = {
            'internal_1': 75, 'internal_2': 72, 'internal_3': 70,
            'assignment': 22, 'prev_sem_gpa': 7.0,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 80
        }
        result = predict_result(data)
        assert result['grade'] == 'B'

    def test_grade_c(self):
        """Internal avg 60-69 should get C."""
        data = {
            'internal_1': 65, 'internal_2': 62, 'internal_3': 60,
            'assignment': 20, 'prev_sem_gpa': 6.5,
            'study_hours_per_day': 2.5, 'extra_activity': False, 'attendance': 78
        }
        result = predict_result(data)
        assert result['grade'] == 'C'

    def test_grade_d(self):
        """Internal avg 50-59 should get D."""
        data = {
            'internal_1': 55, 'internal_2': 52, 'internal_3': 50,
            'assignment': 18, 'prev_sem_gpa': 5.5,
            'study_hours_per_day': 1.5, 'extra_activity': False, 'attendance': 75
        }
        result = predict_result(data)
        assert result['grade'] == 'D'

    def test_grade_f(self):
        """Internal avg < 50 should get F."""
        data = {
            'internal_1': 30, 'internal_2': 25, 'internal_3': 20,
            'assignment': 10, 'prev_sem_gpa': 4.0,
            'study_hours_per_day': 0.5, 'extra_activity': False, 'attendance': 40
        }
        result = predict_result(data)
        assert result['grade'] == 'F'


class TestExtraActivityBonus:
    """Tests for extra-curricular activity bonus."""

    def test_extra_activity_upgrades_risk(self):
        """Extra activity should upgrade risk level for passing students."""
        data = {
            'internal_1': 50, 'internal_2': 55, 'internal_3': 45,
            'assignment': 20, 'prev_sem_gpa': 6.0,
            'study_hours_per_day': 1.5, 'extra_activity': True, 'attendance': 80
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Pass'
        # Without extra_activity it would be Medium, with it should be Low
        assert result['risk_level'] == 'Low'


class TestAttendancePenalty:
    """Tests for attendance penalty."""

    def test_attendance_below_75_increases_risk(self):
        """Attendance < 75% should increase risk for passing students."""
        data = {
            'internal_1': 85, 'internal_2': 90, 'internal_3': 80,
            'assignment': 28, 'prev_sem_gpa': 8.5,
            'study_hours_per_day': 4, 'extra_activity': False, 'attendance': 70
        }
        result = predict_result(data)
        assert result['prediction_result'] == 'Pass'
        # Would be Low risk but attendance penalty makes it Medium
        assert result['risk_level'] == 'Medium'


class TestSuggestions:
    """Tests for suggestion generation."""

    def test_suggestions_for_low_marks(self):
        """Low internal marks should generate tutoring suggestion."""
        data = {
            'internal_1': 30, 'internal_2': 25, 'internal_3': 35,
            'assignment': 10, 'prev_sem_gpa': 4.0,
            'study_hours_per_day': 0.5, 'extra_activity': False, 'attendance': 40
        }
        result = predict_result(data)
        assert len(result['suggestions']) > 0
        assert any('internal' in s.lower() or 'tutoring' in s.lower() for s in result['suggestions'])

    def test_suggestions_for_good_student(self):
        """Good student should get positive suggestion."""
        data = {
            'internal_1': 95, 'internal_2': 92, 'internal_3': 90,
            'assignment': 28, 'prev_sem_gpa': 9.0,
            'study_hours_per_day': 5, 'extra_activity': True, 'attendance': 95
        }
        result = predict_result(data)
        assert any('great' in s.lower() or 'excellent' in s.lower() for s in result['suggestions'])

    def test_low_attendance_suggestion(self):
        """Low attendance should generate an attendance-related suggestion."""
        data = {
            'internal_1': 30, 'internal_2': 25, 'internal_3': 35,
            'assignment': 20, 'prev_sem_gpa': 7.0,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 40
        }
        result = predict_result(data)
        assert any('attendance' in s.lower() for s in result['suggestions'])


class TestReturnStructure:
    """Tests for return value structure."""

    def test_return_has_all_keys(self):
        """predict_result should return dict with all expected keys."""
        data = {
            'internal_1': 70, 'internal_2': 75, 'internal_3': 80,
            'assignment': 25, 'prev_sem_gpa': 7.5,
            'study_hours_per_day': 3, 'extra_activity': True, 'attendance': 85
        }
        result = predict_result(data)
        assert 'prediction_result' in result
        assert 'risk_level' in result
        assert 'grade' in result
        assert 'internal_avg' in result
        assert 'attendance' in result
        assert 'suggestions' in result

    def test_prediction_result_is_pass_or_fail(self):
        """prediction_result should be either 'Pass' or 'Fail'."""
        data = {
            'internal_1': 70, 'internal_2': 75, 'internal_3': 80,
            'assignment': 25, 'prev_sem_gpa': 7.5,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 85
        }
        result = predict_result(data)
        assert result['prediction_result'] in ('Pass', 'Fail')

    def test_risk_level_is_valid(self):
        """risk_level should be Low, Medium, or High."""
        data = {
            'internal_1': 70, 'internal_2': 75, 'internal_3': 80,
            'assignment': 25, 'prev_sem_gpa': 7.5,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 85
        }
        result = predict_result(data)
        assert result['risk_level'] in ('Low', 'Medium', 'High')

    def test_internal_avg_calculation(self):
        """Internal average should be correctly calculated."""
        data = {
            'internal_1': 60, 'internal_2': 70, 'internal_3': 80,
            'assignment': 25, 'prev_sem_gpa': 7.0,
            'study_hours_per_day': 3, 'extra_activity': False, 'attendance': 85
        }
        result = predict_result(data)
        expected_avg = round((60 + 70 + 80) / 3, 2)
        assert result['internal_avg'] == expected_avg
