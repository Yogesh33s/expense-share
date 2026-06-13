"""
Routes package initialization - register all blueprints
"""
from .auth import auth_bp
from .groups import groups_bp
from .expenses import expenses_bp
from .imports import imports_bp
from .balances import balances_bp

__all__ = [
    'auth_bp',
    'groups_bp',
    'expenses_bp',
    'imports_bp',
    'balances_bp'
]