"""
Expense service
"""
from src.backend.models import Expense, ExpenseSplit, Group, User
from src.backend.models.database import db
from datetime import datetime, date
import json

class ExpenseService:
    """Service for expense management"""

    @staticmethod
    def create_expense(group_id, paid_by_user_id, description, amount, currency,
                      exchange_rate, expense_date, split_type, notes=None,
                      split_details=None, is_settlement=False):
        """Create a new expense"""
        # Validate inputs
        group = Group.query.get(group_id)
        if not group:
            return None, "Group not found"

        paid_by_user = User.query.get(paid_by_user_id)
        if not paid_by_user:
            return None, "User not found"

        # Validate currency
        if currency not in ['INR', 'USD']:
            return None, "Invalid currency"

        # Validate split_type
        if split_type not in ['equal', 'unequal', 'percentage', 'share']:
            return None, "Invalid split type"

        # Calculate base currency amount
        amount_base_currency = float(amount) * float(exchange_rate)

        # Create expense
        expense = Expense(
            group_id=group_id,
            paid_by_user_id=paid_by_user_id,
            description=description,
            amount=amount,
            currency=currency,
            exchange_rate=exchange_rate,
            amount_base_currency=amount_base_currency,
            date=expense_date,
            split_type=split_type,
            notes=notes,
            is_settlement=is_settlement
        )
        db.session.add(expense)
        db.session.flush()  # Get the ID without committing

        # Process splits if provided and not a settlement
        if split_details and not is_settlement:
            success, error = ExpenseService._process_splits(
                expense.id, split_type, split_details, amount
            )
            if not success:
                db.session.rollback()
                return None, error

        db.session.commit()
        return expense, None

    @staticmethod
    def _process_splits(expense_id, split_type, split_details, total_amount):
        """Process split details and create expense splits"""
        from src.backend.services import GroupService  # Avoid circular import

        try:
            if split_type == 'equal':
                return ExpenseService._process_equal_splits(expense_id, split_details, total_amount)
            elif split_type == 'percentage':
                return ExpenseService._process_percentage_splits(expense_id, split_details, total_amount)
            elif split_type == 'share':
                return ExpenseService._process_share_splits(expense_id, split_details, total_amount)
            elif split_type == 'unequal':
                return ExpenseService._process_unequal_splits(expense_id, split_details, total_amount)
            else:
                return False, f"Unsupported split type: {split_type}"
        except Exception as e:
            return False, f"Error processing splits: {str(e)}"

    @staticmethod
    def _process_equal_splits(expense_id, split_details, total_amount):
        """Process equal splits"""
        # For equal splits, split_details might be empty or contain user list
        # If empty, we'll need to get users from the group (handled elsewhere)
        # For now, assume split_details contains semicolon-separated user names

        if not split_details or split_details.strip() == '':
            # This should be handled by getting group members
            return False, "Equal split requires user list in split_details"

        user_names = [name.strip() for name in split_details.split(';') if name.strip()]
        if not user_names:
            return False, "No users specified for equal split"

        # Validate users exist
        users = []
        for name in user_names:
            user = User.query.filter_by(name=name).first()
            if not user:
                return False, f"User not found: {name}"
            users.append(user)

        # Calculate equal share
        share_amount = float(total_amount) / len(users)

        # Create splits
        for user in users:
            split = ExpenseSplit(
                expense_id=expense_id,
                user_id=user.id,
                share_amount=share_amount,
                share_percentage=(100.0 / len(users)),
                share_count=1.0,
                calculated_amount=share_amount
            )
            db.session.add(split)

        return True, None

    @staticmethod
    def _process_percentage_splits(expense_id, split_details, total_amount):
        """Process percentage splits"""
        # Parse format: "Name X%; Name Y%; ..."
        if not split_details or split_details.strip() == '':
            return False, "Percentage split requires split_details"

        # Split by semicolon
        parts = [part.strip() for part in split_details.split(';') if part.strip()]
        if not parts:
            return False, "No split parts found"

        total_percentage = 0
        splits_data = []

        for part in parts:
            # Each part should be "Name X%"
            if '%' not in part:
                return False, f"Invalid percentage format: {part}"

            # Extract name and percentage
            name_part = part.split('%')[0].strip()
            percent_str = ''

            # Extract the percentage number from the end
            for i in range(len(name_part) - 1, -1, -1):
                if name_part[i].isdigit() or name_part[i] == '.':
                    percent_str = name_part[i] + percent_str
                else:
                    break

            if not percent_str:
                return False, f"Missing percentage value in: {part}"

            try:
                percentage = float(percent_str)
                if percentage < 0 or percentage > 100:
                    return False, f"Percentage out of range (0-100): {percentage}"

                total_percentage += percentage

                # Find user
                user = User.query.filter_by(name=name_part).first()
                if not user:
                    return False, f"User not found: {name_part}"

                share_amount = float(total_amount) * (percentage / 100.0)

                splits_data.append({
                    'user_id': user.id,
                    'share_amount': share_amount,
                    'share_percentage': percentage,
                    'share_count': None,
                    'calculated_amount': share_amount
                })
            except ValueError:
                return False, f"Invalid percentage number: {percent_str}"

        # Check if total percentage is approximately 100%
        if abs(total_percentage - 100.0) > 0.01:
            return False, f"Percentage sum is {total_percentage}%, expected 100%"

        # Create splits
        for split_data in splits_data:
            split = ExpenseSplit(**split_data)
            db.session.add(split)

        return True, None

    @staticmethod
    def _process_share_splits(expense_id, split_details, total_amount):
        """Process share splits"""
        # Parse format: "Name X; Name Y; ..."
        if not split_details or split_details.strip() == '':
            return False, "Share split requires split_details"

        # Split by semicolon
        parts = [part.strip() for part in split_details.split(';') if part.strip()]
        if not parts:
            return False, "No split parts found"

        total_shares = 0
        splits_data = []

        for part in parts:
            # Each part should be "Name X" where X is a number
            if not part:
                continue

            # Split into name and share parts
            last_space_idx = part.rfind(' ')
            if last_space_idx == -1:
                return False, f"Invalid share format: missing share value in '{part}'"

            name_part = part[:last_space_idx].strip()
            share_str = part[last_space_idx+1:].strip()

            if not name_part:
                return False, f"Empty name in share detail: '{part}'"

            if not share_str:
                return False, f"Missing share value in: '{part}'"

            try:
                shares = float(share_str)
                if shares <= 0:
                    return False, f"Share value must be positive: {shares}"

                total_shares += shares

                # Find user
                user = User.query.filter_by(name=name_part).first()
                if not user:
                    return False, f"User not found: {name_part}"

                splits_data.append({
                    'user_id': user.id,
                    'share_amount': 0,  # Will calculate later
                    'share_percentage': 0,  # Will calculate later
                    'share_count': shares,
                    'calculated_amount': 0  # Will calculate later
                })
            except ValueError:
                return False, f"Invalid share number: {share_str}"

        if total_shares == 0:
            return False, "Total shares must be greater than zero"

        # Calculate actual amounts
        for split_data in splits_data:
            share_percentage = (split_data['share_count'] / total_shares) * 100.0
            share_amount = float(total_amount) * (split_data['share_count'] / total_shares)

            split_data['share_percentage'] = share_percentage
            split_data['share_amount'] = share_amount
            split_data['calculated_amount'] = share_amount

        # Create splits
        for split_data in splits_data:
            split = ExpenseSplit(**split_data)
            db.session.add(split)

        return True, None

    @staticmethod
    def _process_unequal_splits(expense_id, split_details, total_amount):
        """Process unequal splits (explicit amounts)"""
        # Parse format: "Name X; Name Y; ..." where X is amount
        if not split_details or split_details.strip() == '':
            return False, "Unequal split requires split_details"

        # Split by semicolon
        parts = [part.strip() for part in split_details.split(';') if part.strip()]
        if not parts:
            return False, "No split parts found"

        total_amount_from_splits = 0.0
        splits_data = []

        for part in parts:
            # Each part should be "Name X" where X is an amount
            if not part:
                continue

            # Split into name and amount parts
            last_space_idx = part.rfind(' ')
            if last_space_idx == -1:
                return False, f"Invalid unequal format: missing amount in '{part}'"

            name_part = part[:last_space_idx].strip()
            amount_str = part[last_space_idx+1:].strip()

            if not name_part:
                return False, f"Empty name in unequal detail: '{part}'"

            if not amount_str:
                return False, f"Missing amount in: '{part}'"

            try:
                # Parse amount (handle commas)
                amount_clean = amount_str.replace(',', '')
                amount = float(amount_clean)
                if amount < 0:
                    return False, f"Negative amount in unequal split: {amount}"

                total_amount_from_splits += amount

                # Find user
                user = User.query.filter_by(name=name_part).first()
                if not user:
                    return False, f"User not found: {name_part}"

                # For unequal splits, percentage is based on share amount
                share_percentage = (amount / float(total_amount)) * 100.0 if float(total_amount) != 0 else 0

                splits_data.append({
                    'user_id': user.id,
                    'share_amount': amount,
                    'share_percentage': share_percentage,
                    'share_count': None,
                    'calculated_amount': amount
                })
            except ValueError:
                return False, f"Invalid amount value: {amount_str}"

        # Check if total amount matches expense amount (allowing for small rounding differences)
        if abs(total_amount_from_splits - float(total_amount)) > 0.01:
            return False, f"Sum of split amounts ({total_amount_from_splits}) does not match expense amount ({total_amount})"

        # Create splits
        for split_data in splits_data:
            split = ExpenseSplit(**split_data)
            db.session.add(split)

        return True, None

    @staticmethod
    def get_expense(expense_id):
        """Get an expense by ID"""
        return Expense.query.get(expense_id)

    @staticmethod
    def get_expenses_by_group(group_id, limit=None, offset=None):
        """Get expenses for a group"""
        query = Expense.query.filter_by(group_id=group_id).order_by(Expense.date.desc())
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_expenses_by_user(user_id, limit=None, offset=None):
        """Get expenses paid by a user"""
        query = Expense.query.filter_by(paid_by_user_id=user_id).order_by(Expense.date.desc())
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def update_expense(expense_id, **kwargs):
        """Update an expense"""
        expense = Expense.query.get(expense_id)
        if not expense:
            return None, "Expense not found"

        # Update fields
        for key, value in kwargs.items():
            if hasattr(expense, key):
                setattr(expense, key, value)

        db.session.commit()
        return expense, None

    @staticmethod
    def delete_expense(expense_id):
        """Delete an expense"""
        expense = Expense.query.get(expense_id)
        if not expense:
            return False, "Expense not found"

        db.session.delete(expense)
        db.session.commit()
        return True, None