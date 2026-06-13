"""
Balances controller
"""
from flask import Blueprint, request, jsonify
from src.backend.services.balances_service import BalancesService
from src.backend.services.auth_service import AuthService
from src.backend.models import User
import os
from datetime import datetime

balances_bp = Blueprint('balances', __name__)

def verify_token(token):
    """Verify token and return user_id (simplified)"""
    # In production, this would validate a JWT token
    # For now, we'll just return a dummy user_id for demonstration
    # This is not secure - in production use proper JWT validation
    if token == "demo-token":
        return 1  # Assume user ID 1 for demo
    return None

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authorization token is required'}), 401

        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Add user_id to request context
        request.current_user_id = user_id
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@balances_bp.route('/<int:group_id>', methods=['GET'])
@require_auth
def get_balances(group_id):
    """Get user balances for a group"""
    # Optional date parameter
    as_of_date_str = request.args.get('as_of_date')
    as_of_date = None
    if as_of_date_str:
        try:
            as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    balances = BalancesService.calculate_user_balances(group_id, as_of_date)
    return jsonify({
        'group_id': group_id,
        'as_of_date': as_of_date.isoformat() if as_of_date else None,
        'balances': balances
    }), 200

@balances_bp.route('/<int:group_id>/settlements', methods=['GET'])
@require_auth
def get_settlement_recommendations(group_id):
    """Get settlement recommendations for a group"""
    # Optional date parameter
    as_of_date_str = request.args.get('as_of_date')
    as_of_date = None
    if as_of_date_str:
        try:
            as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    settlements = BalancesService.generate_settlement_recommendations(group_id, as_of_date)
    net_balance = BalancesService.get_net_group_balance(group_id, as_of_date)

    return jsonify({
        'group_id': group_id,
        'as_of_date': as_of_date.isoformat() if as_of_date else None,
        'net_group_balance': net_balance,
        'settlements': settlements
    }), 200

@balances_bp.route('/<int:group_id>/net-balance', methods=['GET'])
@require_auth
def get_net_group_balance(group_id):
    """Get net balance for a group"""
    # Optional date parameter
    as_of_date_str = request.args.get('as_of_date')
    as_of_date = None
    if as_of_date_str:
        try:
            as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    net_balance = BalancesService.get_net_group_balance(group_id, as_of_date)
    return jsonify({
        'group_id': group_id,
        'as_of_date': as_of_date.isoformat() if as_of_date else None,
        'net_group_balance': net_balance
    }), 200