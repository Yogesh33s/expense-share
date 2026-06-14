"""
Main Flask application file
"""
import sys
import os
from flask import Flask
from flask_cors import CORS

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backend.models.database import db
from src.backend.controllers.auth_controller import auth_bp
from src.backend.controllers.groups_controller import groups_bp
from src.backend.controllers.expenses_controller import expenses_bp
from src.backend.controllers.imports_controller import imports_bp
from src.backend.controllers.balances_controller import balances_bp


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Enable CORS
    CORS(app)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY',
        'dev-secret-key-change-in-production'
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///expense_share.db'
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB uploads

    # Initialize database
    db.init_app(app)

    # Register API blueprints
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
        return {
            'message': 'Shared Expenses API',
            'version': '1.0',
            'status': 'running'
        }

    @app.route('/health')
    def health():
        return {
            'status': 'healthy',
            'service': 'shared-expenses-api'
        }

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )