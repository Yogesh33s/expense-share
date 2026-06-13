"""
Imports controller
"""
from flask import Blueprint, request, jsonify, send_file
from src.backend.services.import_service import ImportService
from src.backend.services.auth_service import AuthService
from src.backend.models import User
import os
import tempfile

imports_bp = Blueprint('imports', __name__)

def verify_token(token):
    """Verify token and return user_id (simplified)"""
    # In production, this would validate a JWT token
    # For now, we'll just return a dummy user_id for demonstration
    # This is not secure - in production use proper JWT validation
    if token == "demo-token":
        return 1  # Assume user ID 1 for demo
    return None

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authorization token is required'}), 401

        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Add user_id to request context
        request.current_user_id = user_id
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@imports_bp.route('/upload', methods=['POST'])
@require_auth
def upload_csv():
    """Upload a CSV file for import"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check file extension
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Only CSV files are allowed'}), 400

    # Save file temporarily
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        # Process the import
        import_service = ImportService()
        group_id = request.form.get('group_id', type=int)
        user_id = request.form.get('user_id', type=int) or request.current_user_id

        import_log, error = import_service.import_csv(temp_file_path, group_id, user_id)

        # Clean up temporary file
        os.unlink(temp_file_path)

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'File uploaded and import processed successfully',
            'import_log': import_log.to_dict()
        }), 201

    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        return jsonify({'error': f'File processing failed: {str(e)}'}), 500

@imports_bp.route('/<int:import_log_id>', methods=['GET'])
@require_auth
def get_import_log(import_log_id):
    """Get an import log by ID"""
    import_service = ImportService()
    import_log = import_service.get_import_log(import_log_id)
    if not import_log:
        return jsonify({'error': 'Import log not found'}), 404

    return jsonify({
        'import_log': import_log.to_dict()
    }), 200

@imports_bp.route('/', methods=['GET'])
@require_auth
def get_import_logs():
    """Get import logs"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    import_service = ImportService()
    import_logs = import_service.get_import_logs(limit, offset)
    return jsonify({
        'import_logs': [log.to_dict() for log in import_logs]
    }), 200

@imports_bp.route('/<int:import_log_id>/anomalies', methods=['GET'])
@require_auth
def get_import_anomalies(import_log_id):
    """Get anomalies for an import log"""
    import_service = ImportService()
    anomalies = import_service.get_import_anomalies(import_log_id)
    return jsonify({
        'anomalies': [anomaly.to_dict() for anomaly in anomalies]
    }), 200

@imports_bp.route('/<int:import_log_id>/report', methods=['GET'])
@require_auth
def get_import_report(import_log_id):
    """Get import report (JSON format)"""
    import_service = ImportService()
    import_log = import_service.get_import_log(import_log_id)
    if not import_log:
        return jsonify({'error': 'Import log not found'}), 404

    # For now, we'll return a simplified report
    # In a full implementation, we would generate a report similar to the core importer
    anomalies = import_service.get_import_anomalies(import_log_id)

    return jsonify({
        'import_log': import_log.to_dict(),
        'anomalies': [anomaly.to_dict() for anomaly in anomalies],
        'anomaly_count': len(anomalies)
    }), 200

@imports_bp.route('/<int:import_log_id>/report/download', methods=['GET'])
@require_auth
def download_import_report(import_log_id):
    """Download import report as file"""
    import_service = ImportService()
    import_log = import_service.get_import_log(import_log_id)
    if not import_log:
        return jsonify({'error': 'Import log not found'}), 404

    # Generate a simple text report for download
    anomalies = import_service.get_import_anomalies(import_log_id)

    report_content = f"""Import Report
====================
File: {import_log.filename}
Status: {import_log.status}
Started: {import_log.import_started_at}
Ended: {import_log.import_ended_at or 'In Progress'}
Total Rows: {import_log.total_rows}
Processed Rows: {import_log.processed_rows}
Skipped Rows: {import_log.skipped_rows}

Anomalies Found: {len(anomalies)}

"""

    for anomaly in anomalies:
        report_content += f"""Row {anomaly.row_number}: {anomaly.anomaly_type} ({anomaly.severity})
  Description: {anomaly.description}
  Original Data: {anomaly.original_data}
  Suggested Fix: {anomaly.suggested_fix or 'None'}
  Applied: {anomaly.was_applied}

"""

    # Create a temporary file for download
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
        temp_file.write(report_content)
        temp_file_path = temp_file.name

    try:
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=f'import_report_{import_log.id}.txt',
            mimetype='text/plain'
        )
    finally:
        # Clean up after sending (Flask handles this in background)
        pass