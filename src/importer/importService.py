from typing import List, Dict, Any, Optional, Tuple
import os
from datetime import datetime

from .csvParser import CSVParser, ParsedExpense
from .validator import ExpenseValidator, ValidationResult
from .transformer import ExpenseTransformer, TransformedExpense
from .reportGenerator import ImportReportGenerator

class ImportService:
    """Main service for importing and processing CSV expense data"""

    def __init__(self, base_currency: str = 'INR'):
        self.parser = CSVParser()
        self.validator = ExpenseValidator()
        self.transformer = ExpenseTransformer(base_currency=base_currency)
        self.report_generator = ImportReportGenerator()
        self.base_currency = base_currency

    def import_expenses(self, csv_file_path: str,
                       generate_reports: bool = True,
                       report_json_path: str = "import-report.json",
                       report_md_path: str = "import-report.md") -> Dict[str, Any]:
        """
        Import expenses from CSV file

        Args:
            csv_file_path: Path to the CSV file
            generate_reports: Whether to generate import reports
            report_json_path: Path for JSON report
            report_md_path: Path for Markdown report

        Returns:
            Dictionary containing import results
        """
        start_time = datetime.now()

        # Initialize results
        result = {
            'success': False,
            'message': '',
            'parsed_expenses': [],
            'validation_results': [],
            'transformed_expenses': [],
            'import_report': None,
            'statistics': {
                'start_time': start_time.isoformat(),
                'end_time': None,
                'duration_ms': None,
                'total_rows': 0,
                'valid_rows': 0,
                'invalid_rows': 0,
                'rows_with_critical_errors': 0,
                'rows_with_errors': 0,
                'rows_with_warnings': 0,
                'rows_with_info': 0
            }
        }

        try:
            # Check if file exists
            if not os.path.exists(csv_file_path):
                result['message'] = f"CSV file not found: {csv_file_path}"
                return result

            # Step 1: Parse CSV
            print(f"Parsing CSV file: {csv_file_path}")
            parsed_expenses = self.parser.parse_csv(csv_file_path)
            result['parsed_expenses'] = parsed_expenses
            result['statistics']['total_rows'] = len(parsed_expenses)

            # Step 2: Validate expenses
            print(f"Validating {len(parsed_expenses)} expenses...")
            validation_results = []
            for expense in parsed_expenses:
                validation_result = self.validator.validate_expense(expense)
                validation_results.append(validation_result)
            result['validation_results'] = validation_results

            # Step 3: Transform valid expenses
            print("Transforming valid expenses...")
            transformed_expenses = []
            for expense, validation in zip(parsed_expenses, validation_results):
                # Check for critical errors that would prevent transformation
                critical_anomalies = [a for a in validation.anomalies if a.severity == 'critical']
                error_anomalies = [a for a in validation.anomalies if a.severity == 'error']

                # Transform if no critical errors (we can still transform with errors/warnings)
                if len(critical_anomalies) == 0:
                    transformed = self.transformer.transform_expense(expense, validation)
                    transformed_expenses.append(transformed)

            result['transformed_expenses'] = transformed_expenses

            # Step 4: Calculate statistics
            valid_count = sum(1 for r in validation_results if r.is_valid)
            result['statistics']['valid_rows'] = valid_count
            result['statistics']['invalid_rows'] = len(validation_results) - valid_count

            # Count by severity
            for validation in validation_results:
                for anomaly in validation.anomalies:
                    if anomaly.severity == 'critical':
                        result['statistics']['rows_with_critical_errors'] += 1
                        break  # Count each row only once per severity level
                for anomaly in validation.anomalies:
                    if anomaly.severity == 'error':
                        result['statistics']['rows_with_errors'] += 1
                        break
                for anomaly in validation.anomalies:
                    if anomaly.severity == 'warning':
                        result['statistics']['rows_with_warnings'] += 1
                        break
                for anomaly in validation.anomalies:
                    if anomaly.severity == 'info':
                        result['statistics']['rows_with_info'] += 1
                        break

            # Step 5: Generate reports if requested
            if generate_reports:
                print("Generating import reports...")
                import_stats = {
                    'processing_duration_ms': 0,  # Will update after
                    'parser_version': '1.0',
                    'validation_rules_applied': len(self.validator.valid_split_types) + 5,  # Approximate
                    'base_currency': self.base_currency
                }

                report_data = self.report_generator.generate_import_report(
                    validation_results=validation_results,
                    transformed_expenses=transformed_expenses,
                    import_stats=import_stats
                )

                result['import_report'] = report_data

                # Save reports to files
                json_path, md_path = self.report_generator.save_reports(
                    report_data,
                    json_path=report_json_path,
                    md_path=report_md_path
                )

                result['report_files'] = {
                    'json': json_path,
                    'markdown': md_path
                }

            # Step 6: Finalize
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            result['statistics']['end_time'] = end_time.isoformat()
            result['statistics']['duration_ms'] = duration_ms

            # Update report with actual duration
            if result['import_report'] and 'import_statistics' in result['import_report']:
                result['import_report']['import_statistics']['processing_duration_ms'] = duration_ms

            result['success'] = True
            result['message'] = f"Successfully imported {len(transformed_expenses)} of {len(parsed_expenses)} expenses"

        except Exception as e:
            result['success'] = False
            result['message'] = f"Import failed: {str(e)}"
            # Still try to save partial results if we have them
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            result['statistics']['end_time'] = end_time.isoformat()
            result['statistics']['duration_ms'] = duration_ms

        return result

    def get_expenses_ready_for_storage(self, import_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get expenses in a format ready for database storage

        Args:
            import_result: Result from import_expenses method

        Returns:
            List of dictionaries ready for database insertion
        """
        if not import_result['success'] or not import_result['transformed_expenses']:
            return []

        storage_ready = []
        for transformed in import_result['transformed_expenses']:
            storage_dict = self.transformer.to_dict(transformed)
            storage_ready.append(storage_dict)

        return storage_ready

# Example usage
if __name__ == "__main__":
    # Test the import service
    import_service = ImportService()

    # Import the CSV
    result = import_service.import_expenses(
        csv_file_path='expenses_export.csv',
        generate_reports=True,
        report_json_path='import-report.json',
        report_md_path='import-report.md'
    )

    print(f"Import Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Parsed Expenses: {len(result['parsed_expenses'])}")
    print(f"Valid Expenses: {result['statistics']['valid_rows']}")
    print(f"Transformed Expenses: {len(result['transformed_expenses'])}")

    if result['success']:
        print(f"Duration: {result['statistics']['duration_ms']} ms")
        if 'report_files' in result:
            print(f"Report files: {result['report_files']}")