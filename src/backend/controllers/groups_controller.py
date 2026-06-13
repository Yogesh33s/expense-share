"""
Groups controller
"""
from flask import Blueprint, request, jsonify
from src.backend.services.group_service import GroupService
from src.backend.services.auth_service import AuthService
from src.backend.models import User
import os

groups_bp = Blueprint('groups', __name__)

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

@groups_bp.route('/', methods=['POST'])
@require_auth
def create_group():
    """Create a new group"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({'error': 'Group name is required'}), 400

    group, error = GroupService.create_group(
        name=name,
        description=description,
        created_by_user_id=request.current_user_id
    )
    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'Group created successfully',
        'group': group.to_dict()
    }), 201

@groups_bp.route('/', methods=['GET'])
@require_auth
def get_groups():
    """Get all groups"""
    groups = GroupService.get_all_groups()
    return jsonify({
        'groups': [group.to_dict() for group in groups]
    }), 200

@groups_bp.route('/<int:group_id>', methods=['GET'])
@require_auth
def get_group(group_id):
    """Get a group by ID"""
    group = GroupService.get_group(group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    return jsonify({
        'group': group.to_dict()
    }), 200

@groups_bp.route('/<int:group_id>', methods=['PUT'])
@require_auth
def update_group(group_id):
    """Update a group"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name = data.get('name')
    description = data.get('description')

    group, error = GroupService.update_group(group_id, name, description)
    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'Group updated successfully',
        'group': group.to_dict()
    }), 200

@groups_bp.route('/<int:group_id>', methods=['DELETE'])
@require_auth
def delete_group(group_id):
    """Delete a group"""
    success, error = GroupService.delete_group(group_id)
    if not success:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'Group deleted successfully'
    }), 200

@groups_bp.route('/<int:group_id>/users', methods=['POST'])
@require_auth
def add_user_to_group(group_id):
    """Add a user to a group"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    membership, error = GroupService.add_user_to_group(group_id, user_id)
    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'User added to group successfully',
        'membership': membership.to_dict() if membership else None
    }), 201

@groups_bp.route('/<int:group_id>/users/<int:user_id>', methods=['DELETE'])
@require_auth
def remove_user_from_group(group_id, user_id):
    """Remove a user from a group"""
    success, error = GroupService.remove_user_from_group(group_id, user_id)
    if not success:
        return jsonify({'error': error}), 400

    return jsonify({
        'message': 'User removed from group successfully'
    }), 200

@groups_bp.route('/<int:group_id>/users', methods=['GET'])
@require_auth
def get_group_users(group_id):
    """Get users in a group"""
    include_former = request.args.get('include_former', 'false').lower() == 'true'
    users = GroupService.get_group_users(group_id, include_former)
    return jsonify({
        'users': [user.to_dict() for user in users]
    }), 200

@groups_bp.route('/users/<int:user_id>/groups', methods=['GET'])
@require_auth
def get_user_groups(user_id):
    """Get groups a user belongs to"""
    include_former = request.args.get('include_former', 'false').lower() == 'true'
    groups = GroupService.get_user_groups(user_id, include_former)
    return jsonify({
        'groups': [group.to_dict() for group in groups]
    }), 200