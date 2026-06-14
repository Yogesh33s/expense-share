import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useParams, useNavigate } from 'react-router-dom';
import './ImportReportViewer.css';

const ImportReportViewer = () => {
  const { user } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const [importLogs, setImportLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [importLog, setImportLog] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [detailLoading, setDetailLoading] = useState(false);

  // Fetch list of import logs (only when viewing the list, i.e., no id)
  useEffect(() => {
    if (id) {
      // If we have an id, we are in detail view, so we don't need the list
      return;
    }
    const fetchImportLogs = async () => {
      try {
        setLoading(true);
        const response = await api.get('/imports/');
        setImportLogs(response.data.import_logs || []);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching import logs:', err);
        setError('Failed to load import logs');
        setLoading(false);
      }
    };

    if (user) {
      fetchImportLogs();
    }
  }, [user, id]);

  // Fetch details of the import log when we have an id
  useEffect(() => {
    if (!id) {
      // If we don't have an id, we are in list view, so we don't need to fetch details
      return;
    }
    const fetchImportLogDetails = async () => {
      try {
        setDetailLoading(true);
        const response = await api.get(`/imports/${id}`);
        setImportLog(response.data.import_log);

        const anomaliesResponse = await api.get(`/imports/${id}/anomalies`);
        setAnomalies(anomaliesResponse.data.anomalies || []);

        setDetailLoading(false);
      } catch (err) {
        console.error('Error fetching import log details:', err);
        setError('Failed to load import log details');
        setDetailLoading(false);
      }
    };

    if (user && id) {
      fetchImportLogDetails();
    }
  }, [user, id]);

  if (loading && !id) {
    return <div className="import-report-viewer-page">Loading...</div>;
  }

  if (error && !id) {
    return <div className="import-report-viewer-page">Error: {error}</div>;
  }

  if (!user) {
    return <div className="import-report-viewer-page">Please log in to view import reports</div>;
  }

  return (
    <div className="import-report-viewer-page">
      {!id ? (
        // List view
        <>
          <div className="import-report-viewer-header">
            <h1>Import Reports</h1>
          </div>

          {importLogs.length === 0 ? (
            <div className="empty-state">
              <p>No import logs found</p>
            </div>
          ) : (
            <div className="import-logs-list">
              {importLogs.map(log => (
                <div key={log.id} className="import-log-card">
                  <div className="import-log-header">
                    <h3>{log.filename}</h3>
                    <span className={`status-${log.status}`}>{log.status}</span>
                  </div>
                  <div className="import-log-body">
                    <p><strong>Started:</strong> {new Date(log.import_started_at).toLocaleString()}</p>
                    {log.import_ended_at && (
                      <p><strong>Ended:</strong> {new Date(log.import_ended_at).toLocaleString()}</p>
                    )}
                    <p><strong>Total Rows:</strong> {log.total_rows}</p>
                    <p><strong>Processed Rows:</strong> {log.processed_rows}</p>
                    <p><strong>Skipped Rows:</strong> {log.skipped_rows}</p>
                  </div>
                  <div className="import-log-actions">
                    <button className="view-btn" onClick={() => navigate(`/imports/${log.id}`)}>
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        // Detail view
        <>
          <div className="import-report-viewer-header">
            <button className="back-btn" onClick={() => navigate('/imports')}>
              ← Back to List
            </button>
            <h1>Import Report Details</h1>
          </div>

          {detailLoading ? (
            <div className="import-report-detail-loading">Loading details...</div>
          ) : (
            <>
              {!importLog ? (
                <div className="import-report-detail-loading">Loading import log details...</div>
              ) : (
                <>
                  <div className="import-report-detail-header">
                    <h2>{importLog.filename}</h2>
                    <p className={`status-${importLog.status}`}>{importLog.status}</p>
                  </div>

                  <div className="import-report-detail-stats">
                    <div className="stat-item">
                      <h3>Started</h3>
                      <p>{new Date(importLog.import_started_at).toLocaleString()}</p>
                    </div>
                    <div className="stat-item">
                      <h3>Ended</h3>
                      <p>{importLog.import_ended_at ? new Date(importLog.import_ended_at).toLocaleString() : 'In Progress'}</p>
                    </div>
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
                      <h3>Anomalies</h3>
                      <p>{anomalies.length}</p>
                    </div>
                  </div>

                  {anomalies.length > 0 && (
                    <div className="import-report-detail-anomalies">
                      <h2>Anomalies Detected</h2>
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
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
};

export default ImportReportViewer;