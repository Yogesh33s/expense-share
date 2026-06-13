"""
Test script to run the import service on the actual CSV file
"""
import os
import sys
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.importer.importService import ImportService

def main():
    print("Testing Import Service on actual CSV file...")

    # Create import service
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

            # Show a snippet of the JSON report
            if os.path.exists('import-report.json'):
                print("\n--- JSON Report Snippet ---")
                with open('import-report.json', 'r') as f:
                    data = json.load(f)
                    print(f"Total rows processed: {data['import_metadata']['total_rows_processed']}")
                    print(f"Valid rows: {data['import_metadata']['valid_rows']}")
                    print(f"Invalid rows: {data['import_metadata']['invalid_rows']}")
                    print(f"Success rate: {data['import_metadata']['success_rate']:.2f}%")

                    # Show first few anomalies
                    anomalies = data['detailed_anomalies']
                    if anomalies:
                        print(f"\nFirst {min(5, len(anomalies))} anomalies:")
                        for i, anomaly in enumerate(anomalies[:5]):
                            print(f"  {i+1}. Row {anomaly['row_number']}: {anomaly['anomaly_type']} ({anomaly['severity']})")
                            print(f"     {anomaly['description']}")
                    else:
                        print("\nNo anomalies detected.")

            # Show a snippet of the Markdown report
            if os.path.exists('import-report.md'):
                print("\n--- Markdown Report Snippet ---")
                with open('import-report.md', 'r') as f:
                    lines = f.readlines()
                    # Show first 20 lines
                    for i, line in enumerate(lines[:20]):
                        print(f"{i+1:2}: {line.rstrip()}")
                    if len(lines) > 20:
                        print("    ...")
    else:
        print(f"Import failed: {result['message']}")

if __name__ == "__main__":
    main()