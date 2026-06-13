"""
Test suite for the CSV importer
"""
import unittest
import os
import sys
import tempfile
from datetime import datetime

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.importer.csvParser import CSVParser, ParsedExpense
from src.importer.validator import ExpenseValidator, ValidationResult, Anomaly
from src.importer.transformer import ExpenseTransformer
from src.importer.reportGenerator import ImportReportGenerator
from src.importer.importService import ImportService

class TestCSVParser(unittest.TestCase):
    """Test cases for CSVParser"""

    def setUp(self):
        self.parser = CSVParser()

    def test_parse_clean_amount(self):
        """Test parsing of clean amount strings"""
        self.assertEqual(self.parser._parse_amount("100.50"), 100.50)
        self.assertEqual(self.parser._parse_amount("1,000"), 1000.0)
        self.assertEqual(self.parser._parse_amount(""), 0.0)

    def test_parse_date_iso(self):
        """Test parsing of ISO format dates"""
        date_obj = self.parser._parse_date("2026-02-01")
        self.assertIsNotNone(date_obj)
        self.assertEqual(date_obj.year, 2026)
        self.assertEqual(date_obj.month, 2)
        self.assertEqual(date_obj.day, 1)

    def test_parse_date_slash(self):
        """Test parsing of slash format dates"""
        date_obj = self.parser._parse_date("01/03/2026")
        self.assertIsNotNone(date_obj)
        self.assertEqual(date_obj.year, 2026)
        self.assertEqual(date_obj.month, 3)
        self.assertEqual(date_obj.day, 1)

    def test_normalize_name(self):
        """Test name normalization"""
        self.assertEqual(self.parser._normalize_name("priya"), "Priya")
        self.assertEqual(self.parser._normalize_name("rohan"), "Rohan")
        self.assertEqual(self.parser._normalize_name("PRIYA"), "Priya")
        self.assertEqual(self.parser._normalize_name("priya s"), "Priya")

    def test_parse_split_with(self):
        """Test parsing of split_with field"""
        names = self.parser._parse_split_with("Aisha;Rohan;Priya")
        self.assertEqual(names, ["Aisha", "Rohan", "Priya"])

        names = self.parser._parse_split_with("Aisha")
        self.assertEqual(names, ["Aisha"])

        names = self.parser._parse_split_with("")
        self.assertEqual(names, [])

class TestExpenseValidator(unittest.TestCase):
    """Test cases for ExpenseValidator"""

    def setUp(self):
        self.validator = ExpenseValidator()

    def test_validate_valid_expense(self):
        """Test validation of a valid expense"""
        # Create a mock parsed expense
        expense = ParsedExpense(
            raw_row={},
            row_number=2,
            date=datetime(2026, 2, 1),
            description="Test expense",
            paid_by="Aisha",
            amount=1000.0,
            currency="INR",
            split_type="equal",
            split_with=["Aisha", "Rohan"],
            split_details="",
            notes=""
        )

        result = self.validator.validate_expense(expense)
        self.assertTrue(result.is_valid)
        # Should have no critical errors
        critical_anomalies = [a for a in result.anomalies if a.severity == 'critical']
        self.assertEqual(len(critical_anomalies), 0)

    def test_validate_missing_paid_by(self):
        """Test validation of expense with missing paid_by"""
        expense = ParsedExpense(
            raw_row={},
            row_number=2,
            date=datetime(2026, 2, 1),
            description="Test expense",
            paid_by="",  # Missing paid_by
            amount=1000.0,
            currency="INR",
            split_type="equal",
            split_with=["Aisha", "Rohan"],
            split_details="",
            notes=""
        )

        result = self.validator.validate_expense(expense)
        self.assertFalse(result.is_valid)
        critical_anomalies = [a for a in result.anomalies if a.severity == 'critical']
        self.assertGreaterEqual(len(critical_anomalies), 1)
        self.assertEqual(critical_anomalies[0].anomaly_type, 'missing_paid_by')

    def test_validate_zero_amount(self):
        """Test validation of zero amount expense"""
        expense = ParsedExpense(
            raw_row={},
            row_number=2,
            date=datetime(2026, 2, 1),
            description="Test expense",
            paid_by="Aisha",
            amount=0.0,  # Zero amount
            currency="INR",
            split_type="equal",
            split_with=["Aisha", "Rohan"],
            split_details="",
            notes=""
        )

        result = self.validator.validate_expense(expense)
        # Zero amount is valid but should generate a warning
        warning_anomalies = [a for a in result.anomalies if a.severity == 'warning' and a.anomaly_type == 'zero_amount']
        self.assertGreaterEqual(len(warning_anomalies), 1)

    def test_validate_negative_amount(self):
        """Test validation of negative amount (refund)"""
        expense = ParsedExpense(
            raw_row={},
            row_number=2,
            date=datetime(2026, 2, 1),
            description="Test refund",
            paid_by="Aisha",
            amount=-500.0,  # Negative amount
            currency="INR",
            split_type="equal",
            split_with=["Aisha"],
            split_details="",
            notes=""
        )

        result = self.validator.validate_expense(expense)
        # Negative amount is valid but should generate info
        info_anomalies = [a for a in result.anomalies if a.severity == 'info' and a.anomaly_type == 'negative_amount_refund']
        self.assertGreaterEqual(len(info_anomalies), 1)

class TestExpenseTransformer(unittest.TestCase):
    """Test cases for ExpenseTransformer"""

    def setUp(self):
        self.transformer = ExpenseTransformer()

    def test_transform_equal_split(self):
        """Test transformation of equal split expense"""
        expense = ParsedExpense(
            raw_row={},
            row_number=2,
            date=datetime(2026, 2, 1),
            description="Test expense",
            paid_by="Aisha",
            amount=3000.0,
            currency="INR",
            split_type="equal",
            split_with=["Rohan", "Priya"],  # Note: payer not in split_with
            split_details="",
            notes=""
        )

        # Create a valid validation result
        validation = ValidationResult(is_valid=True, anomalies=[])

        transformed = self.transformer.transform_expense(expense, validation)

        self.assertEqual(transformed.description, "Test expense")
        self.assertEqual(transformed.paid_by, "Aisha")
        self.assertEqual(transformed.amount, 3000.0)
        self.assertEqual(transformed.currency, "INR")
        self.assertEqual(transformed.split_type, "equal")
        self.assertFalse(transformed.is_settlement)

        # Should have splits for Rohan and Priya
        self.assertEqual(len(transformed.splits), 2)
        # Each should get half of the amount
        for split in transformed.splits:
            self.assertEqual(split['share_amount'], 1500.0)
            self.assertEqual(split['share_percentage'], 50.0)

    def test_transform_percentage_split(self):
        """Test transformation of percentage split expense"""
        expense = ParsedExpense(
            raw_row={},
            row_number=2,
            date=datetime(2026, 2, 1),
            description="Test expense",
            paid_by="Aisha",
            amount=1000.0,
            currency="INR",
            split_type="percentage",
            split_with=["Aisha", "Rohan", "Priya"],
            split_details="Aisha 50%; Rohan 30%; Priya 20%",
            notes=""
        )

        validation = ValidationResult(is_valid=True, anomalies=[])
        transformed = self.transformer.transform_expense(expense, validation)

        self.assertEqual(len(transformed.splits), 3)
        # Check Aisha's split (50%)
        aisha_split = next((s for s in transformed.splits if s['user_name'] == 'Aisha'), None)
        self.assertIsNotNone(aisha_split)
        self.assertEqual(aisha_split['share_amount'], 500.0)
        self.assertEqual(aisha_split['share_percentage'], 50.0)

        # Check Rohan's split (30%)
        rohan_split = next((s for s in transformed.splits if s['user_name'] == 'Rohan'), None)
        self.assertIsNotNone(rohan_split)
        self.assertEqual(rohan_split['share_amount'], 300.0)
        self.assertEqual(rohan_split['share_percentage'], 30.0)

    def test_transform_settlement_detection(self):
        """Test detection of settlement expenses"""
        expense = ParsedExpense(
            raw_row={},
            row_number=2,
            date=datetime(2026, 2, 1),
            description="Rohan paid Aisha back",
            paid_by="Rohan",
            amount=5000.0,
            currency="INR",
            split_type="",  # Empty split_type
            split_with=["Aisha"],  # Only the payee
            split_details="",
            notes="this is a settlement not an expense??"
        )

        validation = ValidationResult(is_valid=True, anomalies=[])
        transformed = self.transformer.transform_expense(expense, validation)

        # Should be detected as a settlement
        self.assertTrue(transformed.is_settlement)

class TestImportReportGenerator(unittest.TestCase):
    """Test cases for ImportReportGenerator"""

    def setUp(self):
        self.generator = ImportReportGenerator()

    def test_generate_report(self):
        """Test report generation"""
        # Create sample validation results
        anomalies = [
            Anomaly(
                row_number=5,
                anomaly_type='duplicate_entry',
                severity='warning',
                description='Duplicate expense',
                original_value='test data',
                field_name=None
            )
        ]
        validation_result = ValidationResult(is_valid=True, anomalies=anomalies)

        report_data = self.generator.generate_import_report([validation_result])

        self.assertIn('import_metadata', report_data)
        self.assertIn('anomaly_summary', report_data)
        self.assertIn('detailed_anomalies', report_data)
        self.assertEqual(report_data['anomaly_summary']['total_anomalies'], 1)

    def test_save_reports(self):
        """Test saving reports to files"""
        # Create minimal report data
        report_data = {
            'import_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_rows_processed': 10,
                'valid_rows': 8,
                'invalid_rows': 2,
                'success_rate': 80.0
            },
            'anomaly_summary': {
                'by_severity': {'warning': 2},
                'by_type': {'duplicate_entry': 2},
                'total_anomalies': 2
            },
            'detailed_anomalies': [],
            'rows_with_issues': [],
            'import_statistics': {}
        }

        # Create temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = os.path.join(temp_dir, "test-report.json")
            md_path = os.path.join(temp_dir, "test-report.md")

            saved_json, saved_md = self.generator.save_reports(
                report_data,
                json_path=json_path,
                md_path=md_path
            )

            # Check that files were created
            self.assertTrue(os.path.exists(saved_json))
            self.assertTrue(os.path.exists(saved_md))

            # Check JSON content
            with open(saved_json, 'r') as f:
                import json
                loaded_data = json.load(f)
                self.assertEqual(loaded_data['import_metadata']['total_rows_processed'], 10)

class TestImportService(unittest.TestCase):
    """Test cases for ImportService"""

    def setUp(self):
        self.import_service = ImportService()

    def test_import_service_initialization(self):
        """Test that ImportService initializes correctly"""
        self.assertIsNotNone(self.import_service.parser)
        self.assertIsNotNone(self.import_service.validator)
        self.assertIsNotNone(self.import_service.transformer)
        self.assertIsNotNone(self.import_service.report_generator)

    def test_import_nonexistent_file(self):
        """Test importing a non-existent file"""
        result = self.import_service.import_expenses('nonexistent.csv')
        self.assertFalse(result['success'])
        self.assertIn('not found', result['message'])

if __name__ == '__main__':
    unittest.main()