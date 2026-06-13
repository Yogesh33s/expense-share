import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from .validator import ValidationResult, Anomaly
from .transformer import TransformedExpense

class ImportReportGenerator:
    """Generates import reports in JSON and Markdown formats"""

    def __init__(self):
        self.report_timestamp = datetime.now()

    def generate_import_report(self, validation_results: List[ValidationResult],
                             transformed_expenses: List[TransformedExpense] = None,
                             import_stats: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive import report

        Args:
            validation_results: List of validation results
            transformed_expenses: List of transformed expenses (optional)
            import_stats: Statistics about the import process (optional)

        Returns:
            Dictionary containing the import report data
        """
        if import_stats is None:
            import_stats = {}

        # Calculate basic statistics
        total_rows = len(validation_results)
        valid_count = sum(1 for r in validation_results if r.is_valid)
        invalid_count = total_rows - valid_count

        # Count anomalies by severity and type
        anomaly_counts = {'critical': 0, 'error': 0, 'warning': 0, 'info': 0}
        anomaly_type_counts = {}

        all_anomalies = []
        for result in validation_results:
            for anomaly in result.anomalies:
                all_anomalies.append({
                    'row_number': anomaly.row_number,
                    'anomaly_type': anomaly.anomaly_type,
                    'severity': anomaly.severity,
                    'description': anomaly.description,
                    'original_value': anomaly.original_value,
                    'suggested_fix': anomaly.suggested_fix,
                    'field_name': anomaly.field_name
                })
                anomaly_counts[anomaly.severity] = anomaly_counts.get(anomaly.severity, 0) + 1
                anomaly_type_counts[anomaly.anomaly_type] = anomaly_type_counts.get(anomaly.anomaly_type, 0) + 1

        # Prepare rows with issues
        rows_with_issues = []
        for i, result in enumerate(validation_results):
            if not result.is_valid or result.anomalies:
                row_issues = []
                for anomaly in result.anomalies:
                    row_issues.append({
                        'type': anomaly.anomaly_type,
                        'severity': anomaly.severity,
                        'description': anomaly.description
                    })
                rows_with_issues.append({
                    'row_number': i + 2,  # CSV row number (header is row 1)
                    'issues': row_issues
                })

        # Calculate expense statistics if we have transformed expenses
        expense_stats = {}
        user_stats = {}
        currency_stats = defaultdict(float)
        split_type_stats = defaultdict(int)

        if transformed_expenses:
            expense_stats = self._calculate_expense_statistics(transformed_expenses)
            user_stats = self._calculate_user_statistics(transformed_expenses)
            currency_stats = self._calculate_currency_statistics(transformed_expenses)
            split_type_stats = self._calculate_split_type_statistics(transformed_expenses)

        # Build the report
        report = {
            'import_metadata': {
                'timestamp': self.report_timestamp.isoformat(),
                'total_rows_processed': total_rows,
                'valid_rows': valid_count,
                'invalid_rows': invalid_count,
                'success_rate': (valid_count / total_rows * 100) if total_rows > 0 else 0
            },
            'expense_statistics': expense_stats,
            'user_statistics': user_stats,
            'currency_statistics': dict(currency_stats),
            'split_type_statistics': dict(split_type_stats),
            'anomaly_summary': {
                'by_severity': anomaly_counts,
                'by_type': anomaly_type_counts,
                'total_anomalies': len(all_anomalies)
            },
            'detailed_anomalies': all_anomalies,
            'rows_with_issues': rows_with_issues,
            'import_statistics': import_stats
        }

        return report

    def _calculate_expense_statistics(self, expenses: List[TransformedExpense]) -> Dict[str, Any]:
        """Calculate statistics about expenses"""
        if not expenses:
            return {}

        amounts = [abs(exp.amount) for exp in expenses if exp.amount is not None]
        base_amounts = [exp.amount_base_currency for exp in expenses if exp.amount_base_currency is not None]

        return {
            'total_expenses': len(expenses),
            'total_amount': sum(amounts),
            'average_amount': sum(amounts) / len(amounts) if amounts else 0,
            'median_amount': sorted(amounts)[len(amounts)//2] if amounts else 0,
            'min_amount': min(amounts) if amounts else 0,
            'max_amount': max(amounts) if amounts else 0,
            'total_base_currency_amount': sum(base_amounts),
            'average_base_currency_amount': sum(base_amounts) / len(base_amounts) if base_amounts else 0,
            'settlement_count': sum(1 for exp in expenses if exp.is_settlement),
            'regular_expense_count': sum(1 for exp in expenses if not exp.is_settlement)
        }

    def _calculate_user_statistics(self, expenses: List[TransformedExpense]) -> Dict[str, Any]:
        """Calculate statistics about users"""
        if not expenses:
            return {}

        # Who paid the most
        payer_totals = defaultdict(float)
        for exp in expenses:
            if exp.paid_by and exp.amount is not None:
                payer_totals[exp.paid_by] += abs(exp.amount)

        # Who appears most in splits
        split_counts = defaultdict(int)
        for exp in expenses:
            for split in exp.splits:
                split_counts[split['user_name']] += 1

        top_payer = max(payer_totals.items(), key=lambda x: x[1]) if payer_totals else None
        most_appeared = max(split_counts.items(), key=lambda x: x[1]) if split_counts else None

        return {
            'unique_payers': len(payer_totals),
            'unique_users_in_splits': len(split_counts),
            'top_payer_by_amount': {
                'user': top_payer[0] if top_payer else None,
                'amount': top_payer[1] if top_payer else 0
            } if top_payer else {},
            'most_frequent_in_splits': {
                'user': most_appeared[0] if most_appeared else None,
                'count': most_appeared[1] if most_appeared else 0
            } if most_appeared else {},
            'payer_totals': dict(payer_totals)
        }

    def _calculate_currency_statistics(self, expenses: List[TransformedExpense]) -> Dict[str, float]:
        """Calculate currency usage statistics"""
        currency_totals = defaultdict(float)
        for exp in expenses:
            if exp.currency and exp.amount is not None:
                currency_totals[exp.currency.upper()] += abs(exp.amount)
        return dict(currency_totals)

    def _calculate_split_type_statistics(self, expenses: List[TransformedExpense]) -> Dict[str, int]:
        """Calculate split type usage statistics"""
        split_type_counts = defaultdict(int)
        for exp in expenses:
            if exp.split_type:
                split_type_counts[exp.split_type.lower()] += 1
        return dict(split_type_counts)

    def generate_json_report(self, report_data: Dict[str, Any]) -> str:
        """
        Generate JSON report string

        Args:
            report_data: Report data dictionary

        Returns:
            JSON formatted string
        """
        return json.dumps(report_data, indent=2, default=str)

    def generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """
        generate Markdown report string

        Args:
            report_data: Report data dictionary

        Returns:
            Markdown formatted string
        """
        md_lines = []

        # Header
        md_lines.append("# Import Report")
        md_lines.append(f"**Generated:** {report_data['import_metadata']['timestamp']}")
        md_lines.append("")

        # Summary
        md_lines.append("## Summary")
        md_lines.append(f"- **Total Rows Processed:** {report_data['import_metadata']['total_rows_processed']}")
        md_lines.append(f"- **Valid Rows:** {report_data['import_metadata']['valid_rows']}")
        md_lines.append(f"- **Invalid Rows:** {report_data['import_metadata']['invalid_rows']}")
        md_lines.append(f"- **Success Rate:** {report_data['import_metadata']['success_rate']:.2f}%")
        md_lines.append("")

        # Expense Statistics
        if report_data.get('expense_statistics'):
            stats = report_data['expense_statistics']
            md_lines.append("## Expense Statistics")
            md_lines.append(f"- **Total Expenses:** {stats.get('total_expenses', 0)}")
            md_lines.append(f"- **Total Amount:** {stats.get('total_amount', 0):.2f}")
            md_lines.append(f"- **Average Expense:** {stats.get('average_amount', 0):.2f}")
            md_lines.append(f"- **Median Expense:** {stats.get('median_amount', 0):.2f}")
            md_lines.append(f"- **Expense Range:** {stats.get('min_amount', 0):.2f} - {stats.get('max_amount', 0):.2f}")
            md_lines.append(f"- **Total in Base Currency (INR):** {stats.get('total_base_currency_amount', 0):.2f}")
            md_lines.append(f"- **Settlements:** {stats.get('settlement_count', 0)}")
            md_lines.append(f"- **Regular Expenses:** {stats.get('regular_expense_count', 0)}")
            md_lines.append("")

        # User Statistics
        if report_data.get('user_statistics'):
            stats = report_data['user_statistics']
            md_lines.append("## User Statistics")
            md_lines.append(f"- **Unique Payers:** {stats.get('unique_payers', 0)}")
            md_lines.append(f"- **Unique Users in Splits:** {stats.get('unique_users_in_splits', 0)}")
            if stats.get('top_payer_by_amount'):
                top = stats['top_payer_by_amount']
                md_lines.append(f"- **Top Payer:** {top['user']} (paid {top['amount']:.2f})")
            if stats.get('most_frequent_in_splits'):
                freq = stats['most_frequent_in_splits']
                md_lines.append(f"- **Most Frequent in Splits:** {freq['user']} (appeared {freq['count']} times)")
            md_lines.append("")

        # Currency Statistics
        if report_data.get('currency_statistics'):
            md_lines.append("## Currency Statistics")
            for currency, amount in sorted(report_data['currency_statistics'].items()):
                md_lines.append(f"- **{currency}:** {amount:.2f}")
            md_lines.append("")

        # Split Type Statistics
        if report_data.get('split_type_statistics'):
            md_lines.append("## Split Type Statistics")
            for split_type, count in sorted(report_data['split_type_statistics'].items()):
                md_lines.append(f"- **{split_type.title()}:** {count}")
            md_lines.append("")

        # Anomaly Summary
        md_lines.append("## Anomaly Summary")
        md_lines.append("### By Severity")
        for severity, count in report_data['anomaly_summary']['by_severity'].items():
            if count > 0:
                md_lines.append(f"- **{severity.capitalize()}:** {count}")
        md_lines.append("")

        md_lines.append("### By Type")
        for anomaly_type, count in sorted(report_data['anomaly_summary']['by_type'].items()):
            md_lines.append(f"- {anomaly_type}: {count}")
        md_lines.append(f"- **Total Anomalies:** {report_data['anomaly_summary']['total_anomalies']}")
        md_lines.append("")

        # Detailed Anomalies (if any)
        if report_data['detailed_anomalies']:
            md_lines.append("## Detailed Anomalies")
            md_lines.append("| Row | Type | Severity | Description | Original Value | Suggested Fix | Field |")
            md_lines.append("|-----|------|----------|-------------|----------------|---------------|-------|")

            for anomaly in report_data['detailed_anomalies']:
                # Truncate long values for table display
                orig_val = str(anomaly['original_value'])
                if len(orig_val) > 50:
                    orig_val = orig_val[:47] + "..."

                fix_val = str(anomaly['suggested_fix']) if anomaly['suggested_fix'] else ""
                if len(fix_val) > 50:
                    fix_val = fix_val[:47] + "..."

                desc_val = anomaly['description']
                if len(desc_val) > 60:
                    desc_val = desc_val[:57] + "..."

                md_lines.append(f"| {anomaly['row_number']} | {anomaly['anomaly_type']} | {anomaly['severity']} | {desc_val} | {orig_val} | {fix_val} | {anomaly['field_name'] or ''} |")

            md_lines.append("")

        # Rows with Issues Summary
        if report_data['rows_with_issues']:
            md_lines.append("## Rows with Issues")
            md_lines.append(f"{len(report_data['rows_with_issues'])} rows had issues:")
            for row_issue in report_data['rows_with_issues'][:10]:  # Show first 10
                md_lines.append(f"- **Row {row_issue['row_number']}:**")
                for issue in row_issue['issues']:
                    md_lines.append(f"  - {issue['type']} ({issue['severity']}): {issue['description']}")
                if len(row_issue['issues']) > 1:
                    md_lines.append(f"  - *And {len(row_issue['issues']) - 1} more issues*")
            if len(report_data['rows_with_issues']) > 10:
                md_lines.append(f"- *And {len(report_data['rows_with_issues']) - 10} more rows with issues*")
            md_lines.append("")

        # Import Statistics (if provided)
        if report_data.get('import_statistics'):
            md_lines.append("## Import Statistics")
            for key, value in report_data['import_statistics'].items():
                md_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            md_lines.append("")

        return "\n".join(md_lines)

    def save_reports(self, report_data: Dict[str, Any],
                    json_path: str = "import-report.json",
                    md_path: str = "import-report.md") -> tuple:
        """
        Save reports to files

        Args:
            report_data: Report data dictionary
            json_path: Path for JSON report
            md_path: Path for Markdown report

        Returns:
            Tuple of (json_path, md_path) if successful
        """
        # Save JSON report
        json_content = self.generate_json_report(report_data)
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_content)

        # Save Markdown report
        md_content = self.generate_markdown_report(report_data)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return json_path, md_path

# Example usage
if __name__ == "__main__":
    from .validator import ValidationResult, Anomaly

    # Create sample validation results for testing
    sample_anomalies = [
        Anomaly(
            row_number=5,
            anomaly_type='duplicate_entry',
            severity='warning',
            description='Duplicate expense detected',
            original_value='2026-02-08,Dinner at Marina Bites,Dev,3200,INR,equal,"Aisha;Rohan;Priya;Dev",,Dev visiting for the weekend',
            suggested_fix='Skip duplicate row',
            field_name=None
        ),
        Anomaly(
            row_number=26,
            anomaly_type='negative_amount_refund',
            severity='info',
            description='Expense amount is negative (refund)',
            original_value=-30.0,
            field_name='amount'
        )
    ]

    sample_result = ValidationResult(
        is_valid=True,
        anomalies=sample_anomalies
    )

    # Generate report
    generator = ImportReportGenerator()
    report_data = generator.generate_import_report([sample_result, ValidationResult(is_valid=True)])

    # Save reports
    json_file, md_file = generator.save_reports(
        report_data,
        json_path="import-report.json",
        md_path="import-report.md"
    )

    print(f"Reports generated:")
    print(f"- JSON: {json_file}")
    print(f"- Markdown: {md_file}")
    print("\nJSON Report Preview:")
    print(json_data[:500] + "..." if len(json_data) > 500 else json_data)