import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import './Expenses.css';

const Expenses = () => {
  const { user } = useAuth();
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [groups, setGroups] = useState([]);

  // Fetch groups for the user
  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const response = await api.get('/groups');
        setGroups(response.data.groups || []);
        // If we have groups, select the first one by default
        if (response.data.groups && response.data.groups.length > 0) {
          setSelectedGroupId(response.data.groups[0].id);
        }
      } catch (err) {
        console.error('Error fetching groups:', err);
        setError('Failed to load groups');
      }
    };

    if (user) {
      fetchGroups();
    }
  }, [user]);

  // Fetch expenses for selected group
  useEffect(() => {
    const fetchExpenses = async () => {
      if (!selectedGroupId) return;

      try {
        setLoading(true);
        const response = await api.get(`/expenses?group_id=${selectedGroupId}`);
        setExpenses(response.data.expenses || []);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching expenses:', err);
        setError('Failed to load expenses');
        setLoading(false);
      }
    };

    if (selectedGroupId) {
      fetchExpenses();
    }
  }, [selectedGroupId]);

  const handleGroupChange = (e) => {
    const groupId = parseInt(e.target.value);
    setSelectedGroupId(groupId);
  };

  if (loading) {
    return <div className="expenses-page">Loading...</div>;
  }

  if (error) {
    return <div className="expenses-page">Error: {error}</div>;
  }

  if (!user) {
    return <div className="expenses-page">Please log in to view expenses</div>;
  }

  return (
    <div className="expenses-page">
      <div className="expenses-header">
        <h1>Expense Management</h1>
        <div className="expenses-controls">
          <select
            value={selectedGroupId || ''}
            onChange={handleGroupChange}
            className="group-select"
          >
            <option value="">Select a group</option>
            {groups.map(group => (
              <option key={group.id} value={group.id}>
                {group.name}
              </option>
            ))}
          </select>
          <button className="add-expense-btn" onClick={() => {
            // TODO: Add expense form modal
            alert('Add expense functionality coming soon');
          }}>
            Add Expense
          </button>
        </div>
      </div>

      {!selectedGroupId ? (
        <div className="no-group-selected">
          <p>Please select a group to view expenses</p>
        </div>
      ) : (
        <div className="expenses-content">
          {expenses.length === 0 ? (
            <div className="no-expenses">
              <p>No expenses found for this group</p>
            </div>
          ) : (
            <div className="expenses-list">
              {expenses.map(expense => (
                <div key={expense.id} className="expense-card">
                  <div className="expense-header">
                    <h3>{expense.description}</h3>
                    <span className="expense-date">{new Date(expense.date).toLocaleDateString()}</span>
                  </div>
                  <div className="expense-details">
                    <p>
                      <strong>Amount:</strong> {expense.amount} {expense.currency}
                    </p>
                    <p>
                      <strong>Split Type:</strong> {expense.split_type}
                    </p>
                    <p>
                      <strong>Paid by:</strong> User ID {expense.paid_by_user_id}
                    </p>
                    {expense.notes && (
                      <p>
                        <strong>Notes:</strong> {expense.notes}
                      </p>
                    )}
                  </div>
                  <div className="expense-actions">
                    <button className="btn-edit" onClick={() => {
                      // TODO: Edit expense
                      alert('Edit functionality coming soon');
                    }}>Edit</button>
                    <button className="btn-delete" onClick={() => {
                      // TODO: Delete expense
                      alert('Delete functionality coming soon');
                    }}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Expenses;