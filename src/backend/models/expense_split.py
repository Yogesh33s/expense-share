"""
ExpenseSplit model - how expenses are split among users
"""
from src.backend.models.database import db
from datetime import datetime

class ExpenseSplit(db.Model):
    __tablename__ = 'expense_splits'

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    share_amount = db.Column(db.Numeric(15, 4), nullable=False)  # Amount user owes (positive) or is credited (negative)
    share_percentage = db.Column(db.Numeric(5, 2), nullable=True)  # Percentage if split_type is percentage
    share_count = db.Column(db.Numeric(10, 4), nullable=True)  # Share count if split_type is share
    calculated_amount = db.Column(db.Numeric(15, 4), nullable=False)  # Final calculated amount after validation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    expense = db.relationship('Expense', back_populates='splits')
    user = db.relationship('User', back_populates='expense_splits')

    # Constraints
    __table_args__ = (
        # For equal splits: share_percentage and share_count are NULL
        # For unequal splits: share_amount is pre-calculated and stored
        # For percentage splits: share_percentage stored, share_amount calculated
        # For share splits: share_count stored, share_amount calculated
    )

    def __repr__(self):
        return f'<ExpenseSplit {self.user.name if self.user else "Unknown"}: {self.share_amount} ({self.share_percentage}% or {self.share_count} shares)>'

    def to_dict(self):
        return {
            'id': self.id,
            'expense_id': self.expense_id,
            'user_id': self.user_id,
            'share_amount': float(self.share_amount) if self.share_amount else None,
            'share_percentage': float(self.share_percentage) if self.share_percentage else None,
            'share_count': float(self.share_count) if self.share_count else None,
            'calculated_amount': float(self.calculated_amount) if self.calculated_amount else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }