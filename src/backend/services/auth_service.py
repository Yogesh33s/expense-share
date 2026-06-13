"""
Authentication service
"""
from src.backend.models import User
from src.backend.models.database import db
import hashlib
import secrets
from datetime import datetime, timedelta

class AuthService:
    """Authentication service for user registration and login"""

    @staticmethod
    def hash_password(password):
        """Hash a password using SHA-256 with a salt"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}${hash_obj.hexdigest()}"

    @staticmethod
    def verify_password(stored_password, provided_password):
        """Verify a password against the stored hash"""
        if not stored_password or '$' not in stored_password:
            return False
        salt, hash_val = stored_password.split('$', 1)
        hash_obj = hashlib.sha256((provided_password + salt).encode())
        return hash_obj.hexdigest() == hash_val

    @staticmethod
    def register_user(name, email, password):
        """Register a new user"""
        # Check if user already exists
        existing_user = User.query.filter(
            (User.name == name) | (User.email == email)
        ).first()
        if existing_user:
            return None, "User with this name or email already exists"

        # Create new user
        password_hash = AuthService.hash_password(password)
        user = User(name=name, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()

        return user, None

    @staticmethod
    def authenticate_user(name, password):
        """Authenticate a user"""
        user = User.query.filter_by(name=name).first()
        if user and AuthService.verify_password(user.password_hash, password):
            return user, None
        return None, "Invalid credentials"

    @staticmethod
    def generate_token(user_id):
        """Generate a simple token for authentication (in production, use JWT)"""
        # This is a simplified token for demonstration
        # In production, use proper JWT tokens with expiration
        payload = f"{user_id}:{secrets.token_hex(32)}:{datetime.utcnow().timestamp()}"
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def verify_token(token):
        """Verify a token (simplified implementation)"""
        # In production, you would decode and validate JWT tokens
        # This is just a placeholder
        return None  # Would return user_id if valid