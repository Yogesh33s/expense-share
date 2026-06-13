"""
GroupMembership model - tracks when users join and leave groups
"""
from src.backend.models.database import db
from datetime import datetime, date

class GroupMembership(db.Model):
    __tablename__ = 'group_memberships'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.Date, nullable=False, default=date.today)
    left_at = db.Column(db.Date, nullable=True)  # NULL means still a member
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    group = db.relationship('Group', back_populates='memberships')
    user = db.relationship('User', back_populates='group_memberships')

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', 'joined_at', name='unique_group_user_join_date'),
        db.CheckConstraint('left_at IS NULL OR left_at > joined_at', name='check_valid_date_range'),
    )

    def __repr__(self):
        return f'<GroupMembership {self.user.name if self.user else "Unknown"} -> {self.group.name if self.group else "Unknown"} ({self.joined_at} to {self.left_at or "present"})>'

    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @property
    def is_current_member(self):
        """Check if user is currently a member of the group"""
        return self.left_at is None

    @property
    def was_member_on_date(self, check_date):
        """Check if user was a member of the group on a specific date"""
        if self.left_at is None:
            return check_date >= self.joined_at
        return self.joined_at <= check_date <= self.left_at