from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from .csvParser import ParsedExpense

@dataclass
class ValidationResult:
    """Result of validating a parsed expense"""
    is_valid: bool
    anomalies: List['Anomaly'] = field(default_factory=list)
    normalized_data: Optional[Dict[str, Any]] = None

@dataclass
class Anomaly:
    """Represents a data anomaly detected during validation"""
    row_number: int
    anomaly_type: str
    severity: str  # info, warning, error, critical
    description: str
    original_value: Any
    suggested_fix: Optional[Any] = None
    field_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'row_number': self.row_number,
            'anomaly_type': self.anomaly_type,
            'severity': self.severity,
            'description': self.description,
            'original_value': self.original_value,
            'suggested_fix': self.suggested_fix,
            'field_name': self.field_name
        }

class ExpenseValidator:
    """Validates parsed expenses and detects anomalies"""

    def __init__(self):
        # Known valid users from the dataset (will be expanded as we parse)
        self.known_users = set()
        self.valid_currencies = {'INR', 'USD'}
        self.valid_split_types = {'equal', 'unequal', 'percentage', 'share'}

    def validate_expense(self, expense: ParsedExpense, all_users: set = None) -> ValidationResult:
        """
        Validate a parsed expense and detect anomalies

        Args:
            expense: ParsedExpense object to validate
            all_users: Set of all known users in the system (for reference validation)

        Returns:
            ValidationResult with validation status and detected anomalies
        """
        if all_users is None:
            all_users = self.known_users

        anomalies = []
        normalized_data = {}

        # Update known users from this expense
        if expense.paid_by:
            self.known_users.add(expense.paid_by)
        for user in expense.split_with:
            if user:
                self.known_users.add(user)

        # Validate each field
        date_anomalies = self._validate_date(expense)
        anomalies.extend(date_anomalies)

        paid_by_anomalies = self._validate_paid_by(expense, all_users)
        anomalies.extend(paid_by_anomalies)

        amount_anomalies = self._validate_amount(expense)
        anomalies.extend(amount_anomalies)

        currency_anomalies = self._validate_currency(expense)
        anomalies.extend(currency_anomalies)

        split_type_anomalies = self._validate_split_type(expense)
        anomalies.extend(split_type_anomalies)

        split_with_anomalies = self._validate_split_with(expense, all_users)
        anomalies.extend(split_with_anomalies)

        split_details_anomalies = self._validate_split_details(expense)
        anomalies.extend(split_details_anomalies)

        # Check for duplicates (would need to be done across all expenses)
        # This is handled separately in the import service

        # Determine if expense is valid (no critical errors)
        critical_anomalies = [a for a in anomalies if a.severity == 'critical']
        is_valid = len(critical_anomalies) == 0

        # Prepare normalized data for storage
        if is_valid or len([a for a in anomalies if a.severity == 'error']) == 0:
            normalized_data = self._get_normalized_data(expense)

        return ValidationResult(
            is_valid=is_valid,
            anomalies=anomalies,
            normalized_data=normalized_data
        )

    def _validate_date(self, expense: ParsedExpense) -> List[Anomaly]:
        """Validate date field"""
        anomalies = []
        if expense.date is None:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='invalid_date_format',
                severity='error',
                description='Could not parse date',
                original_value=expense.raw_row.get('date', ''),
                field_name='date'
            ))
        elif expense.date.year < 2020 or expense.date.year > 2030:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='invalid_date_range',
                severity='warning',
                description='Date is outside reasonable range',
                original_value=expense.date.isoformat(),
                field_name='date'
            ))
        return anomalies

    def _validate_paid_by(self, expense: ParsedExpense, all_users: set) -> List[Anomaly]:
        """Validate paid_by field"""
        anomalies = []
        if not expense.paid_by:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='missing_paid_by',
                severity='critical',
                description='Paid by field is empty',
                original_value=expense.raw_row.get('paid_by', ''),
                field_name='paid_by'
            ))
        elif expense.paid_by not in all_users and all_users:
            # This is a new user, which is okay
            pass
        return anomalies

    def _validate_amount(self, expense: ParsedExpense) -> List[Anomaly]:
        """Validate amount field"""
        anomalies = []
        if expense.amount == 0:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='zero_amount',
                severity='warning',
                description='Expense amount is zero',
                original_value=expense.amount,
                field_name='amount'
            ))
        elif expense.amount < 0:
            # Negative amounts are refunds, which are valid but should be noted
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='negative_amount_refund',
                severity='info',
                description='Expense amount is negative (refund)',
                original_value=expense.amount,
                field_name='amount'
            ))
        return anomalies

    def _validate_currency(self, expense: ParsedExpense) -> List[Anomaly]:
        """Validate currency field"""
        anomalies = []
        if not expense.currency:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='empty_currency',
                severity='warning',
                description='Currency field is empty',
                original_value=expense.raw_row.get('currency', ''),
                field_name='currency'
            ))
            # Suggest default based on context
            anomalies[-1].suggested_fix = 'INR'
        elif expense.currency not in self.valid_currencies:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='invalid_currency',
                severity='warning',
                description=f'Currency {expense.currency} is not commonly used',
                original_value=expense.currency,
                field_name='currency',
                suggested_fix='INR'  # Default to INR
            ))
        return anomalies

    def _validate_split_type(self, expense: ParsedExpense) -> List[Anomaly]:
        """Validate split_type field"""
        anomalies = []
        if not expense.split_type:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='empty_split_type',
                severity='error',
                description='Split type is empty',
                original_value=expense.raw_row.get('split_type', ''),
                field_name='split_type'
            ))
            # Try to infer from split_details
            if expense.split_details and ('%' in expense.split_details or ';' in expense.split_details):
                anomalies[-1].suggested_fix = 'percentage' if '%' in expense.split_details else 'share'
            else:
                anomalies[-1].suggested_fix = 'equal'
        elif expense.split_type not in self.valid_split_types:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='invalid_split_type',
                severity='error',
                description=f'Split type {expense.split_type} is not valid',
                original_value=expense.split_type,
                field_name='split_type',
                suggested_fix='equal'  # Default fallback
            ))
        return anomalies

    def _validate_split_with(self, expense: ParsedExpense, all_users: set) -> List[Anomaly]:
        """Validate split_with field"""
        anomalies = []
        if not expense.split_with:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='empty_split_with',
                severity='error',
                description='Split with field is empty',
                original_value=expense.raw_row.get('split_with', ''),
                field_name='split_with'
            ))
        else:
            # Check for empty names
            empty_names = [name for name in expense.split_with if not name.strip()]
            if empty_names:
                anomalies.append(Anomaly(
                    row_number=expense.row_number,
                    anomaly_type='empty_name_in_split_with',
                    severity='warning',
                    description='Empty name found in split with',
                    original_value=expense.raw_row.get('split_with', ''),
                    field_name='split_with'
                ))

            # Check for unknown users (if we have a established user set)
            # For now, we'll allow new users as they might be legitimate
            # In a real system, we might want to flag these for review

        return anomalies

    def _normalize_name(self, name: str) -> str:
        """Normalize participant name"""
        if not name:
            return ''

        # Clean whitespace
        cleaned = name.strip()

        # Handle known variations
        lower_name = cleaned.lower()
        # Known variations from the dataset
        name_variations = {
            'priya': 'Priya',
            'rohan': 'Rohan',
            'priya s': 'Priya',
        }

        if lower_name in name_variations:
            return name_variations[lower_name]

        # Convert to proper case (first letter of each word capitalized)
        return ' '.join(word.capitalize() for word in cleaned.split())

    def _validate_split_details(self, expense: ParsedExpense) -> List[Anomaly]:
        """Validate split_details field"""
        anomalies = []

        # If split_details is empty but we have split_with, that might be okay for equal splits
        if not expense.split_details and expense.split_type == 'equal' and expense.split_with:
            # This is actually valid - equal split with no details means equal distribution
            pass
        elif not expense.split_details and expense.split_type != 'equal':
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='missing_split_details',
                severity='error',
                description=f'Split details missing for {expense.split_type} split',
                original_value=expense.raw_row.get('split_details', ''),
                field_name='split_details'
            ))
        else:
            # Validate split_details format based on split_type
            if expense.split_type == 'percentage':
                anomalies.extend(self._validate_percentage_details(expense))
            elif expense.split_type == 'share':
                anomalies.extend(self._validate_share_details(expense))
            elif expense.split_type == 'unequal':
                anomalies.extend(self._validate_unequal_details(expense))
            # For equal splits, split_details is optional

        return anomalies

    def _validate_percentage_details(self, expense: ParsedExpense) -> List[Anomaly]:
        """Validate percentage-based split details"""
        anomalies = []
        details = expense.split_details.strip()

        if not details:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='empty_percentage_details',
                severity='error',
                description='Percentage details are empty',
                original_value=expense.raw_row.get('split_details', ''),
                field_name='split_details'
            ))
            return anomalies

        # Parse percentage format: "Name X%; Name Y%; ..."
        try:
            # Split by semicolon first
            parts = [part.strip() for part in details.split(';') if part.strip()]
            total_percentage = 0
            seen_users = set()

            for part in parts:
                # Each part should be "Name X%"
                if '%' not in part:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='invalid_percentage_format',
                        severity='error',
                        description=f'Percentage format invalid: missing % in "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                # Extract name and percentage
                # Find the % symbol
                percent_idx = part.find('%')
                if percent_idx == -1:
                    continue

                # Extract everything before the %
                name_part = part[:percent_idx].strip()
                if not name_part:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='empty_name_in_percentage',
                        severity='error',
                        description=f'Empty name in percentage detail: "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                # Extract the percentage number (should be at the end of name_part)
                # Find the last space that separates name from number
                last_space_idx = name_part.rfind(' ')
                if last_space_idx == -1:
                    # No space found, assume the whole thing is the percentage
                    percent_str = name_part
                    name_part = ""  # This will be caught below
                else:
                    percent_str = name_part[last_space_idx+1:].strip()
                    name_part = name_part[:last_space_idx].strip()

                if not name_part:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='empty_name_in_percentage',
                        severity='error',
                        description=f'Empty name in percentage detail: "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                try:
                    percentage = float(percent_str)
                    if percentage < 0 or percentage > 100:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='invalid_percentage_range',
                            severity='error',
                            description=f'Percentage out of range (0-100): {percentage}',
                            original_value=details,
                            field_name='split_details'
                        ))
                        break
                    total_percentage += percentage

                    # Normalize and track user
                    normalized_name = self._normalize_name(name_part)
                    if normalized_name in seen_users:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='duplicate_user_in_split',
                            severity='warning',
                            description=f'Duplicate user in split: {normalized_name}',
                            original_value=details,
                            field_name='split_details'
                        ))
                    seen_users.add(normalized_name)

                except ValueError:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='invalid_percentage_number',
                        severity='error',
                        description=f'Invalid percentage number: {percent_str}',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

            # Check if total percentage is approximately 100%
            if not anomalies and abs(total_percentage - 100) > 0.01:
                anomalies.append(Anomaly(
                    row_number=expense.row_number,
                    anomaly_type='percentage_sum_not_100',
                    severity='warning',
                    description=f'Percentage sum is {total_percentage}%, expected 100%',
                    original_value=details,
                    field_name='split_details',
                    suggested_fix=f'Adjust percentages to sum to 100%'
                ))

            # Check if all users in split_with are accounted for
            if not anomalies:
                split_with_set = set(self._normalize_name(name) for name in expense.split_with)
                if split_with_set != seen_users:
                    missing_in_details = split_with_set - seen_users
                    extra_in_details = seen_users - split_with_set
                    if missing_in_details:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='missing_users_in_split_details',
                            severity='error',
                            description=f'Users in split_with not found in split_details: {missing_in_details}',
                            original_value=details,
                            field_name='split_details'
                        ))
                    if extra_in_details:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='extra_users_in_split_details',
                            severity='warning',
                            description=f'Users in split_details not found in split_with: {extra_in_details}',
                            original_value=details,
                            field_name='split_details'
                        ))

        except Exception as e:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='percentage_parsing_error',
                severity='error',
                description=f'Error parsing percentage details: {str(e)}',
                original_value=details,
                field_name='split_details'
            ))

        return anomalies

    def _validate_share_details(self, expense: ParsedExpense) -> List[Anomaly]:
        """Validate share-based split details"""
        anomalies = []
        details = expense.split_details.strip()

        if not details:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='empty_share_details',
                severity='error',
                description='Share details are empty',
                original_value=expense.raw_row.get('split_details', ''),
                field_name='split_details'
            ))
            return anomalies

        # Parse share format: "Name X; Name Y; ..."
        try:
            parts = [part.strip() for part in details.split(';') if part.strip()]
            total_shares = 0
            seen_users = set()

            for part in parts:
                # Each part should be "Name X" where X is a number
                if not part:
                    continue

                # Split into name and share parts
                # Find the last space that separates name from number
                last_space_idx = part.rfind(' ')
                if last_space_idx == -1:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='invalid_share_format',
                        severity='error',
                        description=f'Invalid share format: missing share value in "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                name_part = part[:last_space_idx].strip()
                share_str = part[last_space_idx+1:].strip()

                if not name_part:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='empty_name_in_share',
                        severity='error',
                        description=f'Empty name in share detail: "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                if not share_str:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='missing_share_value',
                        severity='error',
                        description=f'Missing share value in: "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                try:
                    shares = float(share_str)
                    if shares <= 0:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='invalid_share_value',
                            severity='error',
                            description=f'Share value must be positive: {shares}',
                            original_value=details,
                            field_name='split_details'
                        ))
                        break
                    total_shares += shares

                    # Normalize and track user
                    normalized_name = self._normalize_name(name_part)
                    if normalized_name in seen_users:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='duplicate_user_in_split',
                            severity='warning',
                            description=f'Duplicate user in split: {normalized_name}',
                            original_value=details,
                            field_name='split_details'
                        ))
                    seen_users.add(normalized_name)

                except ValueError:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='invalid_share_number',
                        severity='error',
                        description=f'Invalid share number: {share_str}',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

            # Check if all users in split_with are accounted for
            if not anomalies and len(seen_users) > 0:
                split_with_set = set(self._normalize_name(name) for name in expense.split_with)
                if split_with_set != seen_users:
                    missing_in_details = split_with_set - seen_users
                    extra_in_details = seen_users - split_with_set
                    if missing_in_details:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='missing_users_in_split_details',
                            severity='error',
                            description=f'Users in split_with not found in split_details: {missing_in_details}',
                            original_value=details,
                            field_name='split_details'
                        ))
                    if extra_in_details:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='extra_users_in_split_details',
                            severity='warning',
                            description=f'Users in split_details not found in split_with: {extra_in_details}',
                            original_value=details,
                            field_name='split_details'
                        ))

        except Exception as e:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='share_parsing_error',
                severity='error',
                description=f'Error parsing share details: {str(e)}',
                original_value=details,
                field_name='split_details'
            ))

        return anomalies

    def _validate_unequal_details(self, expense: ParsedExpense) -> List[Anomaly]:
        """Validate unequal split details (explicit amounts)"""
        anomalies = []
        details = expense.split_details.strip()

        if not details:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='missing_unequal_details',
                severity='error',
                description='Unequal split requires explicit amounts in split_details',
                original_value=expense.raw_row.get('split_details', ''),
                field_name='split_details'
            ))
            return anomalies

        # Parse unequal format: "Name X; Name Y; ..." where X is amount
        try:
            parts = [part.strip() for part in details.split(';') if part.strip()]
            total_amount = 0
            seen_users = set()

            for part in parts:
                # Each part should be "Name X" where X is an amount
                if not part:
                    continue

                # Split into name and amount parts
                last_space_idx = part.rfind(' ')
                if last_space_idx == -1:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='invalid_unequal_format',
                        severity='error',
                        description=f'Invalid unequal format: missing amount in "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                name_part = part[:last_space_idx].strip()
                amount_str = part[last_space_idx+1:].strip()

                if not name_part:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='empty_name_in_unequal',
                        severity='error',
                        description=f'Empty name in unequal detail: "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                if not amount_str:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='missing_amount_in_unequal',
                        severity='error',
                        description=f'Missing amount in: "{part}"',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

                try:
                    # Parse amount (handle commas)
                    amount_clean = amount_str.replace(',', '')
                    amount = float(amount_clean)
                    if amount < 0:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='negative_amount_in_unequal',
                            severity='warning',
                            description=f'Negative amount in unequal split: {amount}',
                            original_value=details,
                            field_name='split_details'
                        ))
                    total_amount += amount

                    # Normalize and track user
                    normalized_name = self._normalize_name(name_part)
                    if normalized_name in seen_users:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='duplicate_user_in_split',
                            severity='warning',
                            description=f'Duplicate user in split: {normalized_name}',
                            original_value=details,
                            field_name='split_details'
                        ))
                    seen_users.add(normalized_name)

                except ValueError:
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='invalid_amount_in_unequal',
                        severity='error',
                        description=f'Invalid amount value: {amount_str}',
                        original_value=details,
                        field_name='split_details'
                    ))
                    break

            # Check if total amount matches expense amount (allowing for small rounding differences)
            if not anomalies and len(seen_users) > 0:
                if abs(total_amount - abs(expense.amount)) > 0.01:  # Allow 0.01 difference for rounding
                    anomalies.append(Anomaly(
                        row_number=expense.row_number,
                        anomaly_type='unequal_amount_mismatch',
                        severity='error',
                        description=f'Sum of split amounts ({total_amount}) does not match expense amount ({abs(expense.amount)})',
                        original_value=details,
                        field_name='split_details'
                    ))

            # Check if all users in split_with are accounted for
            if not anomalies and len(seen_users) > 0:
                split_with_set = set(self._normalize_name(name) for name in expense.split_with)
                if split_with_set != seen_users:
                    missing_in_details = split_with_set - seen_users
                    extra_in_details = seen_users - split_with_set
                    if missing_in_details:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='missing_users_in_split_details',
                            severity='error',
                            description=f'Users in split_with not found in split_details: {missing_in_details}',
                            original_value=details,
                            field_name='split_details'
                        ))
                    if extra_in_details:
                        anomalies.append(Anomaly(
                            row_number=expense.row_number,
                            anomaly_type='extra_users_in_split_details',
                            severity='warning',
                            description=f'Users in split_details not found in split_with: {extra_in_details}',
                            original_value=details,
                            field_name='split_details'
                        ))

        except Exception as e:
            anomalies.append(Anomaly(
                row_number=expense.row_number,
                anomaly_type='unequal_parsing_error',
                severity='error',
                description=f'Error parsing unequal details: {str(e)}',
                original_value=details,
                field_name='split_details'
            ))

        return anomalies

    def _get_normalized_data(self, expense: ParsedExpense) -> Dict[str, Any]:
        """Get normalized data for storage"""
        return {
            'date': expense.date.isoformat() if expense.date else None,
            'description': expense.description,
            'paid_by': expense.paid_by,
            'amount': expense.amount,
            'currency': expense.currency,
            'split_type': expense.split_type,
            'split_with': expense.split_with,
            'split_details': expense.split_details,
            'notes': expense.notes,
            'normalized_names': True
        }

# Example usage
if __name__ == "__main__":
    from .csvParser import CSVParser, ParsedExpense

    # Test with sample data
    parser = CSVParser()
    validator = ExpenseValidator()

    # Parse the CSV
    expenses = parser.parse_csv('expenses_export.csv')

    # Validate each expense
    validation_results = []
    for expense in expenses:
        result = validator.validate_expense(expense)
        validation_results.append(result)
        if not result.is_valid:
            print(f"Invalid expense at row {expense.row_number}: {expense.description}")
            for anomaly in result.anomalies:
                print(f"  - {anomaly.anomaly_type}: {anomaly.description}")

    valid_count = sum(1 for r in validation_results if r.is_valid)
    print(f"\nValidation complete: {valid_count}/{len(expenses)} expenses valid")