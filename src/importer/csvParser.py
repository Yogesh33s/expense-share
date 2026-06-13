import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ParsedExpense:
    """Represents a parsed expense record from CSV"""
    raw_row: Dict[str, str]
    row_number: int
    date: Optional[datetime]
    description: str
    paid_by: str
    amount: float
    currency: str
    split_type: str
    split_with: List[str]
    split_details: str
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'raw_row': self.raw_row,
            'row_number': self.row_number,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'paid_by': self.paid_by,
            'amount': self.amount,
            'currency': self.currency,
            'split_type': self.split_type,
            'split_with': self.split_with,
            'split_details': self.split_details,
            'notes': self.notes
        }

class CSVParser:
    """Parses CSV file and handles data normalization"""

    def __init__(self):
        self.name_variations = {
            'priya': 'Priya',
            'rohan': 'Rohan',
            'priya s': 'Priya',
            # Add more variations as discovered
        }

    def parse_csv(self, file_path: str) -> List[ParsedExpense]:
        """
        Parse CSV file and return list of parsed expenses

        Args:
            file_path: Path to CSV file

        Returns:
            List of ParsedExpense objects
        """
        parsed_expenses = []

        with open(file_path, 'r', encoding='utf-8') as file:
            # Try to detect delimiter
            sample = file.read(1024)
            file.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.DictReader(file, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 since header is row 1
                try:
                    parsed_expense = self._parse_row(row, row_num)
                    parsed_expenses.append(parsed_expense)
                except Exception as e:
                    # In a real implementation, we'd log this as an anomaly
                    # For now, we'll raise it to be handled upstream
                    raise ValueError(f"Error parsing row {row_num}: {str(e)}") from e

        return parsed_expenses

    def _parse_row(self, row: Dict[str, str], row_number: int) -> ParsedExpense:
        """Parse a single CSV row"""
        # Extract and clean fields
        date_str = self._clean_string(row.get('date', ''))
        description = self._clean_string(row.get('description', ''))
        paid_by = self._clean_string(row.get('paid_by', ''))
        amount_str = self._clean_string(row.get('amount', ''))
        currency = self._clean_string(row.get('currency', ''))
        split_type = self._clean_string(row.get('split_type', ''))
        split_with_str = self._clean_string(row.get('split_with', ''))
        split_details = self._clean_string(row.get('split_details', ''))
        notes = self._clean_string(row.get('notes', ''))

        # Parse date
        date = self._parse_date(date_str)

        # Parse amount (handle commas, etc.)
        amount = self._parse_amount(amount_str)

        # Normalize currency
        currency = self._normalize_currency(currency)

        # Normalize split_type
        split_type = self._normalize_split_type(split_type)

        # Parse split_with (semicolon-separated list)
        split_with = self._parse_split_with(split_with_str)

        # Normalize names in split_with
        split_with = [self._normalize_name(name) for name in split_with if name.strip()]

        # Normalize paid_by
        paid_by = self._normalize_name(paid_by) if paid_by else ''

        return ParsedExpense(
            raw_row=row,
            row_number=row_number,
            date=date,
            description=description,
            paid_by=paid_by,
            amount=amount,
            currency=currency,
            split_type=split_type,
            split_with=split_with,
            split_details=split_details,
            notes=notes
        )

    def _clean_string(self, value: Any) -> str:
        """Clean and normalize string value"""
        if value is None:
            return ''
        return str(value).strip()

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string with multiple format support"""
        if not date_str:
            return None

        # Remove any extra whitespace
        date_str = date_str.strip()

        # Try multiple date formats
        date_formats = [
            '%Y-%m-%d',        # 2026-02-01
            '%d/%m/%Y',        # 01/03/2026
            '%m/%d/%Y',        # 01/03/2026 (US format)
            '%d-%b-%Y',        # 01-Mar-2026
            '%b %d, %Y',       # Mar 01, 2026
            '%d %b %Y',        # 01 Mar 2026
            '%d %b',           # Mar 14 (assume current year)
        ]

        for fmt in date_formats:
            try:
                if fmt == '%d %b' and len(date_str.split()) == 2:
                    # Handle Mar 14 format - assume current year
                    parsed_date = datetime.strptime(date_str, fmt)
                    # Use current year, but we should ideally infer from context
                    # For now, we'll use 2026 as we know the data is from 2026
                    parsed_date = parsed_date.replace(year=2026)
                    return parsed_date
                else:
                    return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # If none of the formats worked, try to extract date with regex
        # Look for patterns like MM/DD/YYYY or DD/MM/YYYY
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    # Try as MM/DD/YYYY first
                    try:
                        month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                        if month <= 12 and day <= 31:
                            return datetime(year, month, day)
                    except ValueError:
                        pass

                    # Try as DD/MM/YYYY
                    try:
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        if month <= 12 and day <= 31:
                            return datetime(year, month, day)
                    except ValueError:
                        pass

        # If we still can't parse it, return None and let validation handle it
        return None

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string, handling commas and other formatting"""
        if not amount_str:
            return 0.0

        # Remove commas and whitespace
        cleaned = amount_str.replace(',', '').strip()

        try:
            return float(cleaned)
        except ValueError:
            # Try to extract number with regex
            number_match = re.search(r'[-+]?\d*\.?\d+', cleaned)
            if number_match:
                try:
                    return float(number_match.group())
                except ValueError:
                    return 0.0
            return 0.0

    def _normalize_currency(self, currency: str) -> str:
        """Normalize currency code"""
        if not currency:
            return 'INR'  # Default based on context

        currency_upper = currency.upper().strip()
        if currency_upper in ['INR', 'USD', 'EUR', 'GBP']:
            return currency_upper
        # Default to INR for unknown currencies based on data context
        return 'INR'

    def _normalize_split_type(self, split_type: str) -> str:
        """Normalize split type"""
        if not split_type:
            return 'equal'  # Default

        split_type_lower = split_type.lower().strip()
        # Map variations to standard types
        if split_type_lower in ['equal', 'equally', 'eq']:
            return 'equal'
        elif split_type_lower in ['unequal', 'unequally', 'custom', 'exact']:
            return 'unequal'
        elif split_type_lower in ['percentage', 'percent', '%', 'perc']:
            return 'percentage'
        elif split_type_lower in ['share', 'shares']:
            return 'share'
        else:
            # Default to equal for unknown types
            return 'equal'

    def _parse_split_with(self, split_with_str: str) -> List[str]:
        """Parse split_with string into list of names"""
        if not split_with_str:
            return []

        # Split by semicolon and clean each name
        names = [name.strip() for name in split_with_str.split(';') if name.strip()]
        return names

    def _normalize_name(self, name: str) -> str:
        """Normalize participant name"""
        if not name:
            return ''

        # Clean whitespace
        cleaned = name.strip()

        # Handle known variations
        lower_name = cleaned.lower()
        if lower_name in self.name_variations:
            return self.name_variations[lower_name]

        # Convert to proper case (first letter of each word capitalized)
        return ' '.join(word.capitalize() for word in cleaned.split())

# Example usage
if __name__ == "__main__":
    parser = CSVParser()
    expenses = parser.parse_csv('expenses_export.csv')
    print(f"Parsed {len(expenses)} expenses")
    for i, expense in enumerate(expenses[:3]):  # Show first 3
        print(f"Expense {i+1}: {expense.description} - {expense.amount} {expense.currency}")