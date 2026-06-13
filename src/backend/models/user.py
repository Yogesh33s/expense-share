"""
User model
"""
from src.backend.models.database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(255), unique=True)
    password_hash = db.Column(db.String(255))  # For authentication
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group_memberships = db.relationship('GroupMembership', back_populates='user', cascade='all, delete-orphan')
    expenses_paid = db.relationship('Expense', back_populates='paid_by_user', foreign_keys='Expense.paid_by_user_id')
    expense_splits = db.relationship('ExpenseSplit', back_populates='user')
    payments_sent = db.relationship('Payment', back_populates='from_user', foreign_keys='Payment.from_user_id')
    payments_received = db.relationship('Payment', back_populates='to_user', foreign_keys='Payment.to_user_id')

    def __repr__(self):
        return f'<User {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }