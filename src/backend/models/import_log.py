"""
ImportLog model - tracks CSV import sessions
"""
from src.backend.models.database import db
from datetime import datetime

class ImportLog(db.Model):
    __tablename__ = 'import_logs'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    import_started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    import_ended_at = db.Column(db.DateTime, nullable=True)
    total_rows = db.Column(db.Integer, nullable=False)  # Total rows in CSV (excluding header)
    processed_rows = db.Column(db.Integer, nullable=False)  # Rows successfully processed
    skipped_rows = db.Column(db.Integer, nullable=False)  # Rows skipped due to errors
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    anomalies = db.relationship('ImportAnomaly', back_populates='import_log', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ImportLog {self.filename}: {self.status} ({self.processed_rows}/{self.total_rows} rows)>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'import_started_at': self.import_started_at.isoformat() if self.import_started_at else None,
            'import_ended_at': self.import_ended_at.isoformat() if self.import_ended_at else None,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'skipped_rows': self.skipped_rows,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }