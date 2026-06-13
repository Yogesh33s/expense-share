"""
Main Flask application file
"""
from flask import Flask
from flask_cors import CORS
import os
from src.backend.models.database import db
from src.backend.routes.auth import auth_bp
from src.backend.routes.groups import groups_bp
from src.backend.routes.expenses import expenses_bp
from src.backend.routes.imports import imports_bp
from src.backend.routes.balances import balances_bp

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///expense_share.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(groups_bp, url_prefix='/api/groups')
    app.register_blueprint(expenses_bp, url_prefix='/api/expenses')
    app.register_blueprint(imports_bp, url_prefix='/api/imports')
    app.register_blueprint(balances_bp, url_prefix='/api/balances')

    # Create tables
    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return {'message': 'Shared Expenses API', 'version': '1.0', 'status': 'running'}

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'shared-expenses-api'}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)