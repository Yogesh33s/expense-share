"""
Balances service - calculates user balances and settlement recommendations
"""
from src.backend.models import User, Group, Expense, ExpenseSplit, Payment
from src.backend.models.database import db
from sqlalchemy import func, and_, or_
from datetime import date

class BalancesService:
    """Service for calculating balances and settlement recommendations"""

    @staticmethod
    def calculate_user_balances(group_id, as_of_date=None):
        """
        Calculate balances for all users in a group
        Positive amount means user should receive money (others owe them)
        Negative amount means user owes money
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get all current members of the group as of the date
        # We'll use a subquery to get current memberships
        from src.backend.models import GroupMembership

        # Subquery for current memberships as of as_of_date
        current_memberships_subquery = db.session.query(
            GroupMembership.user_id
        ).filter(
            GroupMembership.group_id == group_id,
            GroupMembership.joined_at <= as_of_date,
            or_(
                GroupMembership.left_at.is_(None),
                GroupMembership.left_at >= as_of_date
            )
        ).subquery()

        # Get all expenses for the group up to as_of_date
        expenses = Expense.query.filter(
            Expense.group_id == group_id,
            Expense.date <= as_of_date,
            Expense.is_settlement == False  # Exclude settlements from expense calculation
        ).all()

        # Get all payments (settlements) for the group up to as_of_date
        payments = Payment.query.filter(
            Payment.group_id == group_id,
            Payment.date <= as_of_date
        ).all()

        # Initialize balances for all current members
        user_ids = db.session.query(current_memberships_subquery.c.user_id).all()
        user_ids = [uid[0] for uid in user_ids]
        balances = {user_id: 0.0 for user_id in user_ids}

        # Process expenses: who paid and who owes
        for expense in expenses:
            # The payer has paid the full amount (positive balance)
            if expense.paid_by_user_id in balances:
                balances[expense.paid_by_user_id] += float(expense.amount)

            # Each split indicates what each user owes (negative balance for them)
            for split in expense.splits:
                if split.user_id in balances:
                    balances[split.user_id] -= float(split.calculated_amount)

        # Process payments: money transferred between users
        for payment in payments:
            # The sender has paid money (negative balance)
            if payment.from_user_id in balances:
                balances[payment.from_user_id] -= float(payment.amount)

            # The receiver has received money (positive balance)
            if payment.to_user_id in balances:
                balances[payment.to_user_id] += float(payment.amount)

        # Convert to list of user balance objects
        result = []
        for user_id, balance in balances.items():
            user = User.query.get(user_id)
            if user:
                result.append({
                    'user_id': user.id,
                    'user_name': user.name,
                    'balance': round(balance, 2),
                    'owes_money': balance < -0.01,  # Owes money (negative)
                    'owed_money': balance > 0.01    # Owed money (positive)
                })

        # Sort by balance (those who owe most first, then those who are owed most)
        result.sort(key=lambda x: x['balance'])

        return result

    @staticmethod
    def generate_settlement_recommendations(group_id, as_of_date=None):
        """
        Generate settlement recommendations to minimize transactions
        Uses a greedy algorithm to settle debts
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get user balances
        user_balances = BalancesService.calculate_user_balances(group_id, as_of_date)

        # Separate debtors and creditors
        debtors = [ub for ub in user_balances if ub['balance'] < -0.01]
        creditors = [ub for ub in user_balances if ub['balance'] > 0.01]

        # Sort debtors by amount owed (most negative first)
        debtors.sort(key=lambda x: x['balance'])
        # Sort creditors by amount owed (most positive first)
        creditors.sort(key=lambda x: x['balance'], reverse=True)

        settlements = []
        i = 0  # debtor index
        j = 0  # creditor index

        while i < len(debtors) and j < len(creditors):
            debtor = debtors[i]
            creditor = creditors[j]

            # Amount to settle is the minimum of what debtor owes and what creditor is owed
            amount_to_settle = min(-debtor['balance'], creditor['balance'])

            if amount_to_settle > 0.01:  # Only settle if amount is significant
                settlements.append({
                    'from_user_id': debtor['user_id'],  # Debtor pays
                    'from_user_name': debtor['user_name'],
                    'to_user_id': creditor['user_id'],  # Creditor receives
                    'to_user_name': creditor['user_name'],
                    'amount': round(amount_to_settle, 2),
                    'note': f'Settlement to balance debts'
                })

                # Update balances
                debtor['balance'] += amount_to_settle
                creditor['balance'] -= amount_to_settle

            # Move to next debtor or creditor if settled
            if abs(debtor['balance']) < 0.01:
                i += 1
            if abs(creditor['balance']) < 0.01:
                j += 1

        return settlements

    @staticmethod
    def get_net_group_balance(group_id, as_of_date=None):
        """Get the net balance for the entire group (should be zero)"""
        if as_of_date is None:
            as_of_date = date.today()

        user_balances = BalancesService.calculate_user_balances(group_id, as_of_date)
        total_balance = sum(ub['balance'] for ub in user_balances)
        return round(total_balance, 2)