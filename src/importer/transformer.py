from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .csvParser import ParsedExpense
from .validator import ValidationResult

@dataclass
class TransformedExpense:
    """Represents an expense ready for database storage"""
    # Core expense data
    description: str
    paid_by: str
    amount: float
    currency: str
    exchange_rate: float
    amount_base_currency: float
    date: Optional[datetime]
    split_type: str
    notes: str
    is_settlement: bool

    # Reference data (will be resolved to IDs later)
    paid_by_name: str
    split_with_names: List[str]

    # Calculated splits
    splits: List[Dict[str, Any]]  # List of {user_name, share_amount, share_percentage, share_count}

    # Metadata
    original_row_number: int
    raw_data: Dict[str, Any]

class ExpenseTransformer:
    """Transforms parsed and validated expenses into storage-ready format"""

    def __init__(self, base_currency: str = 'INR'):
        self.base_currency = base_currency
        # Exchange rates (as of 2026, approximate)
        self.exchange_rates = {
            'INR': 1.0,
            'USD': 83.0,  # 1 USD = 83 INR
            'EUR': 90.0,  # 1 EUR = 90 INR (approximate)
            'GBP': 105.0, # 1 GBP = 105 INR (approximate)
        }

    def transform_expense(self, expense: ParsedExpense, validation_result: ValidationResult) -> TransformedExpense:
        """
        Transform a parsed expense into storage-ready format

        Args:
            expense: ParsedExpense object
            validation_result: Validation result from validator

        Returns:
            TransformedExpense ready for storage
        """
        # Determine if this is a settlement
        is_settlement = self._is_settlement(expense)

        # Calculate exchange rate and base currency amount
        exchange_rate = self.exchange_rates.get(expense.currency, 1.0)
        amount_base_currency = abs(expense.amount) * exchange_rate

        # Calculate splits based on split type
        splits = self._calculate_splits(expense)

        return TransformedExpense(
            description=expense.description,
            paid_by=expense.paid_by,
            amount=expense.amount,
            currency=expense.currency,
            exchange_rate=exchange_rate,
            amount_base_currency=amount_base_currency,
            date=expense.date,
            split_type=expense.split_type,
            notes=expense.notes,
            is_settlement=is_settlement,
            paid_by_name=expense.paid_by,
            split_with_names=expense.split_with.copy(),
            splits=splits,
            original_row_number=expense.row_number,
            raw_data=expense.to_dict()
        )

    def _is_settlement(self, expense: ParsedExpense) -> bool:
        """Determine if an expense is actually a settlement/payment"""
        # Check for explicit settlement indicators
        if not expense.split_type or expense.split_type.strip() == '':
            # Empty split_type often indicates settlement
            return True

        # Check if split_with contains only the payer (self-payment or single person)
        if len(expense.split_with) == 1 and expense.split_with[0] == expense.paid_by:
            return True

        # Check description for settlement keywords
        settlement_keywords = ['paid back', 'owes me', 'settle', 'repay', 'refund from']
        desc_lower = expense.description.lower()
        if any(keyword in desc_lower for keyword in settlement_keywords):
            return True

        # Check if amount matches a pattern of settlement (often round numbers)
        # This is more heuristic and might not be reliable

        return False

    def _calculate_splits(self, expense: ParsedExpense) -> List[Dict[str, Any]]:
        """Calculate how the expense should be split among users"""
        splits = []

        if not expense.split_with:
            return splits

        # For settlements, typically no splits needed (or just the payer)
        if self._is_settlement(expense):
            # Settlements are between payer and payee, handled separately
            return splits

        # Calculate based on split type
        if expense.split_type == 'equal':
            splits = self._calculate_equal_splits(expense)
        elif expense.split_type == 'percentage':
            splits = self._calculate_percentage_splits(expense)
        elif expense.split_type == 'share':
            splits = self._calculate_share_splits(expense)
        elif expense.split_type == 'unequal':
            splits = self._calculate_unequal_splits(expense)
        else:
            # Default to equal split
            splits = self._calculate_equal_splits(expense)

        return splits

    def _calculate_equal_splits(self, expense: ParsedExpense) -> List[Dict[str, Any]]:
        """Calculate equal splits"""
        splits = []
        if not expense.split_with:
            return splits

        # For equal splits, divide amount equally among all users in split_with
        # Note: Typically the payer is NOT included in the split (they paid, others owe them)
        # But we need to check the data to see how it's structured

        # Looking at the data, it seems like split_with includes everyone who should share the cost
        # Including the payer in some cases, but not in others
        # For now, we'll assume split_with includes all participants, and we'll adjust logic elsewhere

        num_users = len(expense.split_with)
        if num_users > 0:
            # For expenses, the amount is what was paid, so others owe their share
            # For refunds (negative amount), it's the opposite
            share_amount = expense.amount / num_users

            for user_name in expense.split_with:
                splits.append({
                    'user_name': user_name,
                    'share_amount': share_amount,
                    'share_percentage': (100.0 / num_users),
                    'share_count': 1.0
                })

        return splits

    def _calculate_percentage_splits(self, expense: ParsedExpense) -> List[Dict[str, Any]]:
        """Calculate percentage-based splits"""
        splits = []
        details = expense.split_details.strip()

        if not details:
            return splits

        try:
            # Parse percentage format: "Name X%; Name Y%; ..."
            parts = [part.strip() for part in details.split(';') if part.strip()]

            for part in parts:
                if '%' not in part:
                    continue

                # Split into name and percentage parts
                # Find the last space before the %
                percent_idx = part.find('%')
                if percent_idx == -1:
                    continue

                # Extract everything before the %
                before_percent = part[:percent_idx].strip()

                # Now split the name and number - the number should be at the end
                # Find the last space that separates name from number
                last_space_idx = before_percent.rfind(' ')
                if last_space_idx == -1:
                    # No space found, assume the whole thing is the name and percentage is missing
                    continue

                name_part = before_percent[:last_space_idx].strip()
                percent_str = before_percent[last_space_idx+1:].strip()

                if not name_part or not percent_str:
                    continue

                try:
                    percentage = float(percent_str)
                    share_amount = expense.amount * (percentage / 100.0)

                    splits.append({
                        'user_name': name_part,
                        'share_amount': share_amount,
                        'share_percentage': percentage,
                        'share_count': None
                    })
                except ValueError:
                    pass  # Skip invalid percentages
        except Exception:
            pass  # Return empty splits on error

        return splits

    def _calculate_share_splits(self, expense: ParsedExpense) -> List[Dict[str, Any]]:
        """Calculate share-based splits"""
        splits = []
        details = expense.split_details.strip()

        if not details:
            return splits

        try:
            # Parse share format: "Name X; Name Y; ..."
            parts = [part.strip() for part in details.split(';') if part.strip()]
            total_shares = 0

            # First pass: calculate total shares
            user_shares = []
            for part in parts:
                if not part:
                    continue

                # Split into name and share parts
                last_space_idx = part.rfind(' ')
                if last_space_idx == -1:
                    continue

                name_part = part[:last_space_idx].strip()
                share_str = part[last_space_idx+1:].strip()

                if not name_part or not share_str:
                    continue

                try:
                    shares = float(share_str)
                    if shares > 0:
                        user_shares.append((name_part, shares))
                        total_shares += shares
                except ValueError:
                    continue

            # Second pass: calculate actual amounts
            if total_shares > 0:
                for user_name, shares in user_shares:
                    share_percentage = (shares / total_shares) * 100.0
                    share_amount = expense.amount * (shares / total_shares)

                    splits.append({
                        'user_name': user_name,
                        'share_amount': share_amount,
                        'share_percentage': share_percentage,
                        'share_count': shares
                    })

        except Exception:
            pass  # Return empty splits on error

        return splits

    def _calculate_unequal_splits(self, expense: ParsedExpense) -> List[Dict[str, Any]]:
        """Calculate unequal splits (explicit amounts)"""
        splits = []
        details = expense.split_details.strip()

        if not details:
            return splits

        try:
            # Parse unequal format: "Name X; Name Y; ..." where X is amount
            parts = [part.strip() for part in details.split(';') if part.strip()]

            for part in parts:
                if not part:
                    continue

                # Split into name and amount parts
                last_space_idx = part.rfind(' ')
                if last_space_idx == -1:
                    continue

                name_part = part[:last_space_idx].strip()
                amount_str = part[last_space_idx+1:].strip()

                if not name_part or not amount_str:
                    continue

                try:
                    # Parse amount (handle commas)
                    amount_clean = amount_str.replace(',', '')
                    share_amount = float(amount_clean)

                    # For unequal splits, the percentage is based on the share amount
                    share_percentage = (share_amount / abs(expense.amount)) * 100.0 if expense.amount != 0 else 0

                    splits.append({
                        'user_name': name_part,
                        'share_amount': share_amount,
                        'share_percentage': share_percentage,
                        'share_count': None
                    })
                except ValueError:
                    continue  # Skip invalid amounts

        except Exception:
            pass  # Return empty splits on error

        return splits

    def batch_transform(self, parsed_expenses: List[ParsedExpense], validation_results: List[ValidationResult]) -> List[TransformedExpense]:
        """
        Transform a batch of parsed expenses

        Args:
            parsed_expenses: List of ParsedExpense objects
            validation_results: List of ValidationResult objects

        Returns:
            List of TransformedExpense objects
        """
        if len(parsed_expenses) != len(validation_results):
            raise ValueError("Number of expenses and validation results must match")

        transformed_expenses = []
        for expense, validation in zip(parsed_expenses, validation_results):
            # Only transform if validation passed or had only warnings
            critical_anomalies = [a for a in validation.anomalies if a.severity == 'critical']
            if len(critical_anomalies) == 0:
                transformed = self.transform_expense(expense, validation)
                transformed_expenses.append(transformed)

        return transformed_expenses

    def to_dict(self, transformed_expense: TransformedExpense) -> Dict[str, Any]:
        """Convert TransformedExpense to dictionary for storage/serialization"""
        return {
            'description': transformed_expense.description,
            'paid_by': transformed_expense.paid_by,
            'amount': transformed_expense.amount,
            'currency': transformed_expense.currency,
            'exchange_rate': transformed_expense.exchange_rate,
            'amount_base_currency': transformed_expense.amount_base_currency,
            'date': transformed_expense.date.isoformat() if transformed_expense.date else None,
            'split_type': transformed_expense.split_type,
            'notes': transformed_expense.notes,
            'is_settlement': transformed_expense.is_settlement,
            'paid_by_name': transformed_expense.paid_by_name,
            'split_with_names': transformed_expense.split_with_names,
            'splits': transformed_expense.splits,
            'original_row_number': transformed_expense.original_row_number,
            'raw_data': transformed_expense.raw_data
        }

# Example usage
if __name__ == "__main__":
    from .csvParser import CSVParser
    from .validator import ExpenseValidator

    # Test with sample data
    parser = CSVParser()
    validator = ExpenseValidator()
    transformer = ExpenseTransformer()

    # Parse the CSV
    expenses = parser.parse_csv('expenses_export.csv')

    # Validate and transform
    transformed_expenses = []
    for expense in expenses:
        validation_result = validator.validate_expense(expense)
        # Only transform if no critical errors
        critical_anomalies = [a for a in validation_result.anomalies if a.severity == 'critical']
        if len(critical_anomalies) == 0:
            transformed = transformer.transform_expense(expense, validation_result)
            transformed_expenses.append(transformed)
            print(f"Transformed: {transformed.description} - {transformed.amount} {transformed.currency}")
            print(f"  Splits: {len(transformed.splits)}")
            for split in transformed.splits[:2]:  # Show first 2 splits
                print(f"    {split['user_name']}: {split['share_amount']} ({split['share_percentage']}%)")

    print(f"\nTransformed {len(transformed_expenses)} expenses")