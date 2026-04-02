"""
Integration tests for Flask routes.
Tests: authentication flows, dashboard access control, student CRUD, and API endpoints.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestRoleSelection:
    """Tests for the role selection page."""

    def test_role_select_page_loads(self, client):
        """Role selection page should return 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_role_select_contains_roles(self, client):
        """Landing page should contain admin, staff, student."""
        response = client.get('/')
        html = response.data.decode()
        assert 'admin' in html.lower() or 'Admin' in html
        assert 'staff' in html.lower() or 'Staff' in html
        assert 'student' in html.lower() or 'Student' in html


class TestUnifiedLogin:
    """Tests for the unified auto-detect login."""

    def test_unified_login_page_loads(self, client):
        """Unified login page should return 200."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_unified_admin_login(self, client, sample_admin):
        """Admin should login through unified endpoint."""
        response = client.post('/login', data={
            'identifier': 'testadmin',
            'password': 'admin123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_unified_staff_login(self, client, sample_staff):
        """Staff should login through unified endpoint."""
        response = client.post('/login', data={
            'identifier': 'teststaff',
            'password': 'staff123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_unified_student_login(self, client, sample_student):
        """Student should login through unified endpoint using reg_no."""
        response = client.post('/login', data={
            'identifier': '2024CSE001',
            'password': 'student123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_unified_wrong_password(self, client, sample_admin):
        """Wrong password should show error."""
        response = client.post('/login', data={
            'identifier': 'testadmin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Invalid' in html or 'error' in html.lower()

    def test_unified_unknown_user(self, client):
        """Unknown identifier should show error."""
        response = client.post('/login', data={
            'identifier': 'nobody',
            'password': 'nopass'
        }, follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Invalid' in html or 'error' in html.lower()


class TestLoginLogout:
    """Tests for login and logout flows."""

    def test_login_page_loads(self, client):
        """Login page should return 200 for each role."""
        for role in ['admin', 'staff', 'student']:
            response = client.get(f'/login/{role}')
            assert response.status_code == 200

    def test_invalid_role_login_redirects(self, client):
        """Invalid role should redirect."""
        response = client.get('/login/hacker', follow_redirects=True)
        assert response.status_code == 200

    def test_admin_login_success(self, client, sample_admin):
        """Admin should be able to login with correct credentials."""
        response = client.post('/login/admin', data={
            'username': 'testadmin',
            'password': 'admin123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_admin_login_wrong_password(self, client, sample_admin):
        """Admin login with wrong password should fail."""
        response = client.post('/login/admin', data={
            'username': 'testadmin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Invalid' in html or 'error' in html.lower()

    def test_staff_login_success(self, client, sample_staff):
        """Staff should be able to login with correct credentials."""
        response = client.post('/login/staff', data={
            'username': 'teststaff',
            'password': 'staff123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_student_login_success(self, client, sample_student):
        """Student should be able to login with correct credentials."""
        response = client.post('/login/student', data={
            'reg_no': '2024CSE001',
            'password': 'student123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_logout(self, client, sample_admin):
        """Logout should redirect to role selection."""
        # Login first
        client.post('/login/admin', data={
            'username': 'testadmin',
            'password': 'admin123'
        })
        # Then logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestDashboardAccess:
    """Tests for dashboard access control."""

    def test_admin_dashboard_requires_login(self, client):
        """Admin dashboard should redirect unauthenticated users."""
        response = client.get('/dashboard/admin')
        assert response.status_code in (302, 401)

    def test_staff_dashboard_requires_login(self, client):
        """Staff dashboard should redirect unauthenticated users."""
        response = client.get('/dashboard/staff')
        assert response.status_code in (302, 401)

    def test_student_dashboard_requires_login(self, client):
        """Student dashboard should redirect unauthenticated users."""
        response = client.get('/dashboard/student')
        assert response.status_code in (302, 401)


class TestStudentCRUD:
    """Tests for student create and delete operations."""

    def _login_staff(self, client, sample_staff):
        """Helper to log in as staff."""
        client.post('/login/staff', data={
            'username': 'teststaff',
            'password': 'staff123'
        })

    def test_add_student(self, client, sample_staff):
        """Staff should be able to add a student."""
        self._login_staff(client, sample_staff)
        response = client.post('/dashboard/staff/add-student', data={
            'reg_no': '2024CSE999',
            'name': 'New Student',
            'dept': 'CSE',
            'year': '1',
            'password': 'test123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_add_student_missing_fields(self, client, sample_staff):
        """Adding student with missing fields should show error."""
        self._login_staff(client, sample_staff)
        response = client.post('/dashboard/staff/add-student', data={
            'reg_no': '',
            'name': '',
            'dept': '',
            'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_delete_student(self, client, sample_staff, sample_student):
        """Staff should be able to delete a student."""
        self._login_staff(client, sample_staff)
        response = client.post(
            f'/dashboard/staff/delete-student/{sample_student.reg_no}',
            follow_redirects=True
        )
        assert response.status_code == 200


class TestPrediction:
    """Tests for prediction functionality."""

    def _login_staff(self, client, sample_staff):
        """Helper to log in as staff."""
        client.post('/login/staff', data={
            'username': 'teststaff',
            'password': 'staff123'
        })

    def test_run_prediction(self, client, sample_staff, sample_student, sample_academic):
        """Running prediction should succeed for student with academic data."""
        self._login_staff(client, sample_staff)
        response = client.post(
            f'/dashboard/staff/predict/{sample_student.reg_no}',
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_prediction_without_marks(self, client, sample_staff, sample_student):
        """Running prediction without marks should show error."""
        self._login_staff(client, sample_staff)
        response = client.post(
            f'/dashboard/staff/predict/{sample_student.reg_no}',
            follow_redirects=True
        )
        assert response.status_code == 200


class TestAPIEndpoints:
    """Tests for REST API endpoints."""

    def _login_admin(self, client, sample_admin):
        """Helper to log in as admin."""
        client.post('/login/admin', data={
            'username': 'testadmin',
            'password': 'admin123'
        })

    def test_api_students_requires_login(self, client):
        """API endpoint should require authentication."""
        response = client.get('/api/v1/students')
        assert response.status_code in (302, 401)

    def test_api_students_list(self, client, sample_admin, sample_student):
        """API should return student list as JSON."""
        self._login_admin(client, sample_admin)
        response = client.get('/api/v1/students')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'pagination' in data

    def test_api_student_detail(self, client, sample_admin, sample_student):
        """API should return student details."""
        self._login_admin(client, sample_admin)
        response = client.get(f'/api/v1/students/{sample_student.reg_no}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['reg_no'] == sample_student.reg_no

    def test_api_student_not_found(self, client, sample_admin):
        """API should return 404 for unknown student."""
        self._login_admin(client, sample_admin)
        response = client.get('/api/v1/students/UNKNOWN_REG')
        assert response.status_code == 404

    def test_api_stats(self, client, sample_admin, sample_student):
        """API should return dashboard stats."""
        self._login_admin(client, sample_admin)
        response = client.get('/api/v1/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'total_students' in data['data']

    def test_api_predict(self, client, sample_admin, sample_student, sample_academic):
        """API predict endpoint should return prediction result."""
        self._login_admin(client, sample_admin)
        response = client.post(f'/api/v1/predict/{sample_student.reg_no}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['prediction_result'] in ('Pass', 'Fail')

    def test_api_search(self, client, sample_admin, sample_student):
        """API should support search parameter."""
        self._login_admin(client, sample_admin)
        response = client.get('/api/v1/students?search=Test')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
