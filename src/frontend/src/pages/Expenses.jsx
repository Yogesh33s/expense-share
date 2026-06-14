import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import ExpenseForm from '../components/ExpenseForm';
import './Expenses.css';
import '../components/ExpenseForm.css';

const Expenses = () => {
  const { user } = useAuth();
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [groups, setGroups] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [formLoading, setFormLoading] = useState(false);

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
    // Reset form when group changes
    setShowForm(false);
    setEditingExpense(null);
  };

  const handleAddExpense = () => {
    setEditingExpense(null);
    setShowForm(true);
  };

  const handleEditExpense = (expense) => {
    setEditingExpense(expense);
    setShowForm(true);
  };

  const handleDeleteExpense = async (expenseId) => {
    if (window.confirm('Are you sure you want to delete this expense?')) {
      try {
        setLoading(true);
        const response = await api.delete(`/expenses/${expenseId}`);
        // Refresh expenses list
        const response2 = await api.get(`/expenses?group_id=${selectedGroupId}`);
        setExpenses(response2.data.expenses || []);
        setLoading(false);
      } catch (err) {
        console.error('Error deleting expense:', err);
        setError('Failed to delete expense');
        setLoading(false);
      }
    }
  };

  const handleSaveExpense = async (data) => {
    setFormLoading(true);
    try {
      let response;
      if (editingExpense) {
        // Update existing expense
        response = await api.put(`/expenses/${editingExpense.id}`, data);
      } else {
        // Create new expense
        response = await api.post('/expenses', data);
      }

      // Refresh expenses list
      const response2 = await api.get(`/expenses?group_id=${selectedGroupId}`);
      setExpenses(response2.data.expenses || []);
      setShowForm(false);
      setEditingExpense(null);
      setFormLoading(false);
    } catch (err) {
      console.error('Error saving expense:', err);
      setError('Failed to save expense');
      setFormLoading(false);
    }
  };

  const handleCancelExpense = () => {
    setShowForm(false);
    setEditingExpense(null);
    setError('');
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
          <button className="add-expense-btn" onClick={handleAddExpense}>
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
            <>
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
                      <button className="btn-edit" onClick={() => handleEditExpense(expense)}>
                        Edit
                      </button>
                      <button className="btn-delete" onClick={() => handleDeleteExpense(expense.id)}>
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Expense Form Modal */}
              {showForm && (
                <div className="form-modal-backdrop" onClick={handleCancelExpense}>
                  <div className="form-modal" onClick={e => e.stopPropagation()}>
                    <ExpenseForm
                      onSave={handleSaveExpense}
                      onCancel={handleCancelExpense}
                      initialData={editingExpense}
                      loading={formLoading}
                    />
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default Expenses;