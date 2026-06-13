"""
Group service
"""
from src.backend.models import Group, GroupMembership, User
from src.backend.models.database import db
from datetime import date

class GroupService:
    """Service for group management"""

    @staticmethod
    def create_group(name, description=None, created_by_user_id=None):
        """Create a new group"""
        # Check if group already exists
        existing_group = Group.query.filter_by(name=name).first()
        if existing_group:
            return None, "Group with this name already exists"

        # Create group
        group = Group(name=name, description=description)
        db.session.add(group)
        db.session.flush()  # Get the ID without committing

        # If a creator is specified, add them as a member
        if created_by_user_id:
            membership = GroupMembership(
                group_id=group.id,
                user_id=created_by_user_id,
                joined_at=date.today()
            )
            db.session.add(membership)

        db.session.commit()
        return group, None

    @staticmethod
    def get_group(group_id):
        """Get a group by ID"""
        return Group.query.get(group_id)

    @staticmethod
    def get_group_by_name(name):
        """Get a group by name"""
        return Group.query.filter_by(name=name).first()

    @staticmethod
    def get_all_groups():
        """Get all groups"""
        return Group.query.all()

    @staticmethod
    def update_group(group_id, name=None, description=None):
        """Update a group"""
        group = Group.query.get(group_id)
        if not group:
            return None, "Group not found"

        if name is not None:
            # Check if new name conflicts with existing group
            existing_group = Group.query.filter(Group.name == name, Group.id != group_id).first()
            if existing_group:
                return None, "Group with this name already exists"
            group.name = name

        if description is not None:
            group.description = description

        db.session.commit()
        return group, None

    @staticmethod
    def delete_group(group_id):
        """Delete a group"""
        group = Group.query.get(group_id)
        if not group:
            return False, "Group not found"

        db.session.delete(group)
        db.session.commit()
        return True, None

    @staticmethod
    def add_user_to_group(group_id, user_id):
        """Add a user to a group"""
        # Check if group and user exist
        group = Group.query.get(group_id)
        user = User.query.get(user_id)
        if not group:
            return None, "Group not found"
        if not user:
            return None, "User not found"

        # Check if user is already a member
        existing_membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            left_at=None  # Only check current membership
        ).first()
        if existing_membership:
            return None, "User is already a member of this group"

        # Add membership
        membership = GroupMembership(
            group_id=group_id,
            user_id=user_id,
            joined_at=date.today()
        )
        db.session.add(membership)
        db.session.commit()
        return membership, None

    @staticmethod
    def remove_user_from_group(group_id, user_id):
        """Remove a user from a group (set left_at to today)"""
        membership = GroupMembership.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            left_at=None  # Only current memberships
        ).first()
        if not membership:
            return False, "User is not a current member of this group"

        membership.left_at = date.today()
        db.session.commit()
        return True, None

    @staticmethod
    def get_group_users(group_id, include_former=False):
        """Get users in a group"""
        query = GroupMembership.query.filter_by(group_id=group_id)
        if not include_former:
            query = query.filter(GroupMembership.left_at.is_(None))  # Only current members

        memberships = query.all()
        return [membership.user for membership in memberships]

    @staticmethod
    def get_user_groups(user_id, include_former=False):
        """Get groups a user belongs to"""
        query = GroupMembership.query.filter_by(user_id=user_id)
        if not include_former:
            query = query.filter(GroupMembership.left_at.is_(None))  # Only current memberships

        memberships = query.all()
        return [membership.group for membership in memberships]