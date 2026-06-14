"""
Expenses controller
"""
from flask import Blueprint, request, jsonify
from src.backend.services.expense_service import ExpenseService
from src.backend.services.auth_service import AuthService
from src.backend.models import User
import os
from datetime import datetime

expenses_bp = Blueprint('expenses', __name__)

def verify_token(token):
    """Verify token and return user_id"""
    from src.backend.services.auth_service import AuthService
    return AuthService.verify_token(token)

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

@expenses_bp.route('/', methods=['POST'])
@require_auth
def create_expense():
    """Create a new expense"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate required fields
    required_fields = ['group_id', 'description', 'amount', 'currency', 'exchange_rate', 'date', 'split_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    try:
        # Parse date
        expense_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    expense, error = ExpenseService.create_expense(
        group_id=data['group_id'],
        paid_by_user_id=request.current_user_id,  # Current user pays by default
        description=data['description'],
        amount=float(data['amount']),
        currency=data['currency'],
        exchange_rate=float(data['exchange_rate']),
        expense_date=expense_date,
        split_type=data['split_type'],
        notes=data.get('notes'),
        split_details=data.get('split_details'),
        is_settlement=data.get('is_settlement', False)
    )

    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'Expense created successfully',
        'expense': expense.to_dict()
    }), 201

@expenses_bp.route('/', methods=['GET'])
@require_auth
def get_expenses():
    """Get expenses with optional filtering"""
    group_id = request.args.get('group_id')
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)

    if user_id:
        # Get expenses paid by user
        expenses = ExpenseService.get_expenses_by_user(int(user_id), limit, offset)
    elif group_id:
        # Get expenses for group
        expenses = ExpenseService.get_expenses_by_group(int(group_id), limit, offset)
    else:
        # Get all expenses (could be a lot, so we limit by default)
        expenses = ExpenseService.get_expenses_by_group(None, limit, offset)  # This would need modification
        # For simplicity, we'll return empty if neither specified
        return jsonify({'error': 'Either group_id or user_id must be specified'}), 400

    return jsonify({
        'expenses': [expense.to_dict() for expense in expenses]
    }), 200

@expenses_bp.route('/<int:expense_id>', methods=['GET'])
@require_auth
def get_expense(expense_id):
    """Get an expense by ID"""
    expense = ExpenseService.get_expense(expense_id)
    if not expense:
        return jsonify({'error': 'Expense not found'}), 404

    return jsonify({
        'expense': expense.to_dict()
    }), 200

@expenses_bp.route('/<int:expense_id>', methods=['PUT'])
@require_auth
def update_expense(expense_id):
    """Update an expense"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    expense, error = ExpenseService.update_expense(expense_id, **data)
    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'Expense updated successfully',
        'expense': expense.to_dict()
    }), 200

@expenses_bp.route('/<int:expense_id>', methods=['DELETE'])
@require_auth
def delete_expense(expense_id):
    """Delete an expense"""
    success, error = ExpenseService.delete_expense(expense_id)
    if not success:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'Expense deleted successfully'
    }), 200