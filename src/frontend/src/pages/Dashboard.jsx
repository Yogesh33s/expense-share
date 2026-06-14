import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // In a real app, we would fetch actual dashboard stats
        // For now, we'll use mock data
        setStats({
          totalGroups: 5,
          totalExpenses: 23,
          totalAmount: 1250.00,
          pendingSettlements: 2
        });
      } catch (err) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Welcome back, {user?.name || 'User'}!</h1>
        <button onClick={logout} className="btn btn-outline">
          Sign Out
        </button>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Groups</h3>
          <p className="stat-value">{stats.totalGroups}</p>
        </div>
        <div className="stat-card">
          <h3>Expenses</h3>
          <p className="stat-value">{stats.totalExpenses}</p>
        </div>
        <div className="stat-card">
          <h3>Total Amount</h3>
          <p className="stat-value">${stats.totalAmount.toFixed(2)}</p>
        </div>
        <div className="stat-card">
          <h3>Pending Settlements</h3>
          <p className="stat-value">{stats.pendingSettlements}</p>
        </div>
      </div>

      <div className="dashboard-modules">
        <div className="module-card">
          <h2>Quick Actions</h2>
          <div className="btn-group">
            <button
              className="btn btn-primary"
              onClick={() => {/* navigate to groups */}}
            >
              Manage Groups
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {/* navigate to expenses */}}
            >
              Add Expense
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {/* navigate to import */}}
            >
              Import CSV
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {/* navigate to balances */}}
            >
              View Balances
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;