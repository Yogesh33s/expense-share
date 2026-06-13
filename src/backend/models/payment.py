"""
Payment model - tracks explicit payment/settlement transactions between users
"""
from src.backend.models.database import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 4), nullable=False)  # Amount transferred (positive)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    exchange_rate = db.Column(db.Numeric(10, 4), nullable=False, default=1.0)  # Rate to base currency
    amount_base_currency = db.Column(db.Numeric(15, 4), nullable=False)  # Amount in base currency (INR)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    group = db.relationship('Group', back_populates='payments')
    from_user = db.relationship('User', back_populates='payments_sent', foreign_keys=[from_user_id])
    to_user = db.relationship('User', back_populates='payments_received', foreign_keys=[to_user_id])

    # Constraints
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='check_positive_amount'),
        db.CheckConstraint('from_user_id != to_user_id', name='check_no_self_payment'),
        db.CheckConstraint("currency IN ('INR', 'USD')", name='check_valid_currency'),
    )

    def __repr__(self):
        return f'<Payment {self.from_user.name if self.from_user else "Unknown"} -> {self.to_user.name if self.to_user else "Unknown"}: {self.amount} {self.currency}>'

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else None,
            'amount_base_currency': float(self.amount_base_currency) if self.amount_base_currency else None,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }