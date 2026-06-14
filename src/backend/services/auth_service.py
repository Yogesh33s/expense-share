"""
Authentication service
"""
from src.backend.models import User
from src.backend.models.database import db
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
import os

class AuthService:
    """Authentication service for user registration and login"""

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key-change-in-production'
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_MINUTES = 60  # Token valid for 60 minutes

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
        """Generate a JWT token for authentication"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(minutes=AuthService.JWT_EXPIRATION_MINUTES),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, AuthService.JWT_SECRET_KEY, algorithm=AuthService.JWT_ALGORITHM)

    @staticmethod
    def verify_token(token):
        """Verify a JWT token and return user_id if valid"""
        try:
            # Decode the token
            payload = jwt.decode(token, AuthService.JWT_SECRET_KEY, algorithms=[AuthService.JWT_ALGORITHM])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Token is invalid
            return None