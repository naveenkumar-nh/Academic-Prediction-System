import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from models.database import db, User, Student


def create_app():
    """Application factory."""
    # Point Flask to the new frontend directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    # Support both local and Railway deployment paths
    frontend_dir = os.path.abspath(os.path.join(base_dir, '../../frontend/python_ui'))
    if not os.path.exists(frontend_dir):
        frontend_dir = os.path.abspath(os.path.join(base_dir, '../../../frontend/python_ui'))
    if not os.path.exists(frontend_dir):
        # Railway: project root is /app, backend is /app/backend/python
        frontend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', 'frontend', 'python_ui'))

    app = Flask(__name__,
                template_folder=os.path.join(frontend_dir, 'templates'),
                static_folder=os.path.join(frontend_dir, 'static'))
    app.config.from_object(Config)

    # Ensure instance directory exists
    os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.unified_login'
    login_manager.login_message_category = 'error'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by session data. Format: 'user_<id>' or 'student_<id>'."""
        if isinstance(user_id, str) and user_id.startswith('student_'):
            student_id = int(user_id.replace('student_', ''))
            return Student.query.get(student_id)
        elif isinstance(user_id, str) and user_id.startswith('user_'):
            uid = int(user_id.replace('user_', ''))
            return User.query.get(uid)
        else:
            # Legacy fallback
            return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)

    # Create database tables and default admin
    with app.app_context():
        db.create_all()
        _create_default_admin()

    return app


def _create_default_admin():
    """Create default admin account if none exists."""
    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('  [INFO] Default admin created: admin / admin123')


app = create_app()

if __name__ == '__main__':
    print('=' * 60)
    print('  Academic Performance Prediction System')
    print('  Running at: http://127.0.0.1:5000')
    print('=' * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
