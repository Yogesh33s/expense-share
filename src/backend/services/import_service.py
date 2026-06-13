"""
Import service - integrates with the existing importer
"""
import os
import json
from src.backend.models import ImportLog, ImportAnomaly, Group, User
from src.backend.models.database import db
from datetime import datetime
import sys

# Add the src directory to the path so we can import the importer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.importer.importService import ImportService as CoreImportService

class ImportService:
    """Service for importing CSV data"""

    def __init__(self):
        self.core_importer = CoreImportService()

    def import_csv(self, file_path, group_id=None, user_id=None):
        """Import a CSV file and store results in the database"""
        # Create import log
        import_log = ImportLog(
            filename=os.path.basename(file_path),
            status='processing'
        )
        db.session.add(import_log)
        db.session.flush()  # Get the ID

        try:
            # Run the import using our core importer
            result = self.core_importer.import_expenses(
                csv_file_path=file_path,
                generate_reports=False  # We'll generate our own reports
            )

            # Update import log with results
            import_log.total_rows = result['statistics']['total_rows']
            import_log.processed_rows = result['statistics']['valid_rows']
            import_log.skipped_rows = result['statistics']['invalid_rows']
            import_log.status = 'completed' if result['success'] else 'failed'

            # Store anomalies
            if result.get('import_report') and 'detailed_anomalies' in result['import_report']:
                for anomaly_data in result['import_report']['detailed_anomalies']:
                    anomaly = ImportAnomaly(
                        import_log_id=import_log.id,
                        row_number=anomaly_data['row_number'],
                        anomaly_type=anomaly_data['anomaly_type'],
                        description=anomaly_data['description'],
                        severity=anomaly_data['severity'],
                        original_data=json.dumps(anomaly_data['original_value']) if anomaly_data['original_value'] is not None else '',
                        suggested_fix=anomaly_data.get('suggested_fix'),
                        was_applied=False  # We don't automatically apply fixes
                    )
                    db.session.add(anomaly)

            # If import was successful and we have a group/user, we could
            # automatically create expenses from the transformed data
            # For now, we'll just store the import log and anomalies
            # The user can then review and import expenses manually

            db.session.commit()

            return import_log, None if result['success'] else result['message']

        except Exception as e:
            import_log.status = 'failed'
            db.session.commit()
            return None, f"Import failed: {str(e)}"

    def get_import_log(self, import_log_id):
        """Get an import log by ID"""
        return ImportLog.query.get(import_log_id)

    def get_import_logs(self, limit=None, offset=None):
        """Get import logs"""
        query = ImportLog.query.order_by(ImportLog.import_started_at.desc())
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_import_anomalies(self, import_log_id):
        """Get anomalies for an import log"""
        return ImportAnomaly.query.filter_by(import_log_id=import_log_id).all()

    def create_expenses_from_import(self, import_log_id, group_id, user_id):
        """
        Create expenses from a successful import
        This would need to be implemented based on how we want to handle
        the transformed expenses from the core importer
        """
        # This is a placeholder - in a full implementation, we would:
        # 1. Get the import log
        # 2. Check if it was successful
        # 3. Transform the data again or retrieve stored transformed data
        # 4. Create expenses using ExpenseService
        # 5. Link them to the import log
        pass