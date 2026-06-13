"""
Expense model
"""
from src.backend.models.database import db
from datetime import datetime

class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    paid_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(15, 4), nullable=False)  # Original amount
    currency = db.Column(db.String(3), nullable=False, default='INR')
    exchange_rate = db.Column(db.Numeric(10, 4), nullable=False, default=1.0)  # Rate to base currency (INR)
    amount_base_currency = db.Column(db.Numeric(15, 4), nullable=False)  # Amount in base currency
    date = db.Column(db.Date, nullable=False)
    split_type = db.Column(db.String(20), nullable=False)  # equal, unequal, percentage, share
    notes = db.Column(db.Text)
    is_settlement = db.Column(db.Boolean, nullable=False, default=False)  # Whether this is a settlement/payment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = db.relationship('Group', back_populates='expenses')
    paid_by_user = db.relationship('User', back_populates='expenses_paid', foreign_keys=[paid_by_user_id])
    splits = db.relationship('ExpenseSplit', back_populates='expense', cascade='all, delete-orphan')

    # Constraints
    __table_args__ = (
        db.CheckConstraint('amount != 0', name='check_nonzero_amount'),
        db.CheckConstraint("currency IN ('INR', 'USD')", name='check_valid_currency'),
        db.CheckConstraint("split_type IN ('equal', 'unequal', 'percentage', 'share')", name='check_valid_split_type'),
    )

    def __repr__(self):
        return f'<Expense {self.description}: {self.amount} {self.currency} on {self.date}>'

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'paid_by_user_id': self.paid_by_user_id,
            'description': self.description,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else None,
            'amount_base_currency': float(self.amount_base_currency) if self.amount_base_currency else None,
            'date': self.date.isoformat() if self.date else None,
            'split_type': self.split_type,
            'notes': self.notes,
            'is_settlement': self.is_settlement,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }