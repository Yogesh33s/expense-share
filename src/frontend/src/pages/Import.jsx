import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import './Import.css';

const Import = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [importLog, setImportLog] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [showAnomalies, setShowAnomalies] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);

  // Fetch groups for the user
  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const response = await api.get('/groups');
        setGroups(response.data.groups || []);
      } catch (err) {
        console.error('Error fetching groups:', err);
      }
    };

    if (user) {
      fetchGroups();
    }
  }, [user]);

  // Fetch import log details if we have an ID
  useEffect(() => {
    const fetchImportLog = async () => {
      if (!importLog) return;

      try {
        setLoading(true);
        const response = await api.get(`/imports/${importLog.id}`);
        setImportLog(response.data.import_log);

        // Fetch anomalies
        const anomaliesResponse = await api.get(`/imports/${importLog.id}/anomalies`);
        setAnomalies(anomaliesResponse.data.anomalies || []);

        setLoading(false);
      } catch (err) {
        console.error('Error fetching import log:', err);
        setError('Failed to load import details');
        setLoading(false);
      }
    };

    if (importLog) {
      fetchImportLog();
    }
  }, [importLog]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    // Reset form when file changes
    setError('');
    setSuccess('');
    setImportLog(null);
    setAnomalies([]);
    setShowAnomalies(false);
    setShowReport(false);
  };

  const handleGroupChange = (e) => {
    const groupId = parseInt(e.target.value);
    setSelectedGroupId(groupId);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    if (!selectedFile) {
      setError('Please select a file to upload');
      setLoading(false);
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      setError('Please select a CSV file');
      setLoading(false);
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Add group_id if selected
      if (selectedGroupId) {
        formData.append('group_id', selectedGroupId);
      }

      const response = await api.post('/imports/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      setSuccess('File uploaded and import processed successfully!');
      setImportLog(response.data.import_log);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'An error occurred during upload');
      setLoading(false);
      console.error('Error uploading file:', err);
    }
  };

  const handleDownloadReport = async () => {
    if (!importLog) return;

    setDownloadLoading(true);
    try {
      const response = await api.get(`/imports/${importLog.id}/report/download`, {
        responseType: 'blob' // Important for binary data
      });

      // Create a blob from the response
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `import_report_${importLog.id}.txt`);
      document.body.appendChild(link);
      link.click();

      // Clean up
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);

      setDownloadLoading(false);
    } catch (err) {
      console.error('Error downloading report:', err);
      setError('Failed to download report');
      setDownloadLoading(false);
    }
  };

  if (loading) {
    return <div className="import-page">Loading...</div>;
  }

  if (error) {
    return <div className="import-page">Error: {error}</div>;
  }

  if (!user) {
    return <div className="import-page">Please log in to access import functionality</div>;
  }

  return (
    <div className="import-page">
      <div className="import-header">
        <h1>CSV Import</h1>
        <p>Import expenses from a CSV file</p>
      </div>

      {!importLog ? (
        <div className="import-upload-section">
          <div className="import-upload-card">
            <h2>Upload CSV File</h2>
            <form onSubmit={handleUpload} className="import-form">
              <div className="form-group">
                <label htmlFor="file">CSV File:</label>
                <input
                  type="file"
                  id="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  required
                  className="file-input"
                />
                <p className="form-help">Please select a CSV file containing expense data</p>
              </div>

              <div className="form-group">
                <label htmlFor="group_id">Group (Optional):</label>
                <select
                  id="group_id"
                  value={selectedGroupId || ''}
                  onChange={handleGroupChange}
                  className="form-select"
                >
                  <option value="">No Group (Import to All Groups)</option>
                  {groups.map(group => (
                    <option key={group.id} value={group.id}>
                      {group.name}
                    </option>
                  ))}
                </select>
                <p className="form-help">Select a group to associate the imported expenses with</p>
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  disabled={loading}
                  className="submit-btn"
                >
                  {loading ? 'Processing...' : 'Upload & Import'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setSelectedGroupId(null);
                    setError('');
                    setSuccess('');
                  }}
                  className="reset-btn"
                >
                  Reset
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : (
        <>
          <div className="import-results-section">
            <div className="import-results-card">
              <h2>Import Results</h2>

              <div className="import-summary">
                <div className="summary-item">
                  <h3>File</h3>
                  <p>{importLog.filename}</p>
                </div>
                <div className="summary-item">
                  <h3>Status</h3>
                  <p className={`status-${importLog.status}`}>{importLog.status}</p>
                </div>
                <div className="summary-item">
                  <h3>Timeline</h3>
                  <p>
                    Started: {new Date(importLog.import_started_at).toLocaleString()}<br/>
                    {importLog.import_ended_at ? (
                      `Ended: {new Date(importLog.import_ended_at).toLocaleString()}`
                    ) : (
                      'In Progress'
                    )}
                  </p>
                </div>
              </div>

              <div className="import-stats">
                <div className="stat-item">
                  <h3>Total Rows</h3>
                  <p>{importLog.total_rows}</p>
                </div>
                <div className="stat-item">
                  <h3>Processed Rows</h3>
                  <p>{importLog.processed_rows}</p>
                </div>
                <div className="stat-item">
                  <h3>Skipped Rows</h3>
                  <p>{importLog.skipped_rows}</p>
                </div>
                <div className="stat-item">
                  <h3>Anomalies Found</h3>
                  <p>{anomalies.length}</p>
                </div>
              </div>

              {anomalies.length > 0 && (
                <div className="anomalies-section">
                  <h3>Anomalies Detected</h3>
                  <button
                    className="toggle-btn"
                    onClick={() => setShowAnomalies(!showAnomalies)}
                  >
                    {showAnomalies ? 'Hide Anomalies' : 'Show Anomalies'}
                  </button>

                  {showAnomalies && (
                    <div className="anomalies-list">
                      {anomalies.map(anomaly => (
                        <div key={anomaly.id} className="anomaly-card">
                          <div className="anomaly-header">
                            <span className="anomaly-type">{anomaly.anomaly_type}</span>
                            <span className="anomaly-severity severity-{anomaly.severity.toLowerCase()}">
                              {anomaly.severity.toUpperCase()}
                            </span>
                          </div>
                          <div className="anomaly-body">
                            <p><strong>Row:</strong> {anomaly.row_number}</p>
                            <p><strong>Description:</strong> {anomaly.description}</p>
                            {anomaly.original_data && (
                              <p>
                                <strong>Original Data:</strong> {anomaly.original_data}
                              </p>
                            )}
                            {anomaly.suggested_fix && (
                              <p>
                                <strong>Suggested Fix:</strong> {anomaly.suggested_fix}
                              </p>
                            )}
                            <p>
                              <strong>Applied:</strong> {anomaly.was_applied ? 'Yes' : 'No'}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="import-actions-section">
            <div className="import-actions-card">
              <h2>Actions</h2>
              <div className="actions-grid">
                <button
                  className="action-btn"
                  onClick={() => {
                    // Reset to upload another file
                    setSelectedFile(null);
                    setSelectedGroupId(null);
                    setImportLog(null);
                    setAnomalies([]);
                    setShowAnomalies(false);
                    setShowReport(false);
                    setError('');
                    setSuccess('');
                  }}
                >
                  Import Another File
                </button>

                <button
                  className="action-btn"
                  onClick={handleDownloadReport}
                  disabled={downloadLoading}
                >
                  {downloadLoading ? 'Generating...' : 'Download Report'}
                </button>

                {/* TODO: Add button to create expenses from import */}
                <button
                  className="action-btn"
                  onClick={() => {
                    alert('Create expenses from import functionality coming soon');
                  }}
                >
                  Create Expenses from Import
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Import;