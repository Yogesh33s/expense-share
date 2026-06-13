"""
ImportAnomaly model - stores anomalies detected during CSV import
"""
from src.backend.models.database import db
from datetime import datetime

class ImportAnomaly(db.Model):
    __tablename__ = 'import_anomalies'

    id = db.Column(db.Integer, primary_key=True)
    import_log_id = db.Column(db.Integer, db.ForeignKey('import_logs.id'), nullable=False)
    row_number = db.Column(db.Integer, nullable=False)  # CSV row number where anomaly occurred (1-based, excluding header)
    anomaly_type = db.Column(db.String(50), nullable=False)  # Type of anomaly
    description = db.Column(db.Text, nullable=False)  # Human-readable description
    severity = db.Column(db.String(20), nullable=False)  # Severity: info, warning, error, critical
    original_data = db.Column(db.Text, nullable=False)  # Original CSV row data (JSON format)
    suggested_fix = db.Column(db.Text, nullable=True)  # Suggested correction (if applicable)
    was_applied = db.Column(db.Boolean, nullable=False, default=False)  # Whether the suggested fix was applied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    import_log = db.relationship('ImportLog', back_populates='anomalies')

    def __repr__(self):
        return f'<ImportAnomaly {self.anomaly_type} at row {self.row_number}: {self.severity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'import_log_id': self.import_log_id,
            'row_number': self.row_number,
            'anomaly_type': self.anomaly_type,
            'description': self.description,
            'severity': self.severity,
            'original_data': self.original_data,
            'suggested_fix': self.suggested_fix,
            'was_applied': self.was_applied,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }