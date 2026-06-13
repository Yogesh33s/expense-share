import json
from typing import List, Dict, Any
from datetime import datetime
from .validator import ValidationResult, Anomaly

class ImportReportGenerator:
    """Generates import reports in JSON and Markdown formats"""

    def __init__(self):
        self.report_timestamp = datetime.now()

    def generate_import_report(self, validation_results: List[ValidationResult],
                             transformed_expenses: List[Any] = None,
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

        # Calculate statistics
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

        # Build the report
        report = {
            'import_metadata': {
                'timestamp': self.report_timestamp.isoformat(),
                'total_rows_processed': total_rows,
                'valid_rows': valid_count,
                'invalid_rows': invalid_count,
                'success_rate': (valid_count / total_rows * 100) if total_rows > 0 else 0
            },
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