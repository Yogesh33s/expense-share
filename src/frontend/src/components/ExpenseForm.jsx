import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

const ExpenseForm = ({ onSave, onCancel, initialData = null }) => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    group_id: '',
    description: '',
    amount: '',
    currency: 'INR',
    exchange_rate: '1.0',
    date: '',
    split_type: 'equal',
    notes: '',
    split_details: '',
    is_settlement: false
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [groups, setGroups] = useState([]);
  const [groupMembers, setGroupMembers] = useState([]);
  const [isEditing, setIsEditing] = useState(!!initialData);

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

  // Fetch group members when group changes
  useEffect(() => {
    if (formData.group_id) {
      const fetchGroupMembers = async () => {
        try {
          const response = await api.get(`/groups/${formData.group_id}/members`);
          setGroupMembers(response.data.members || []);
        } catch (err) {
          console.error('Error fetching group members:', err);
          setGroupMembers([]);
        }
      };

      fetchGroupMembers();
    } else {
      setGroupMembers([]);
    }
  }, [formData.group_id]);

  // Initialize form with existing data if editing
  useEffect(() => {
    if (initialData) {
      setFormData({
        ...formData,
        group_id: initialData.group_id?.toString() || '',
        description: initialData.description || '',
        amount: initialData.amount?.toString() || '',
        currency: initialData.currency || 'INR',
        exchange_rate: initialData.exchange_rate?.toString() || '1.0',
        date: initialData.date || '',
        split_type: initialData.split_type || 'equal',
        notes: initialData.notes || '',
        split_details: '', // This would need to be generated from splits
        is_settlement: initialData.is_settlement || false
      });
      setIsEditing(true);
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Validate required fields
      if (!formData.group_id) {
        throw new Error('Please select a group');
      }
      if (!formData.description.trim()) {
        throw new Error('Description is required');
      }
      if (!formData.amount || parseFloat(formData.amount) <= 0) {
        throw new Error('Amount must be greater than zero');
      }
      if (!formData.date) {
        throw new Error('Date is required');
      }

      // Prepare data for API
      const expenseData = {
        group_id: parseInt(formData.group_id),
        description: formData.description.trim(),
        amount: parseFloat(formData.amount),
        currency: formData.currency,
        exchange_rate: parseFloat(formData.exchange_rate),
        date: formData.date,
        split_type: formData.split_type,
        notes: formData.notes.trim(),
        split_details: formData.split_details.trim(),
        is_settlement: formData.is_settlement
      };

      let response;
      if (isEditing) {
        // TODO: Implement update expense API call
        // For now, just show a message
        alert('Update expense functionality coming soon');
        response = { data: { message: 'Expense updated successfully' } };
      } else {
        response = await api.post('/expenses', expenseData);
      }

      setLoading(false);
      onSave(response.data);
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.error || err.message || 'An error occurred');
      console.error('Error saving expense:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="expense-form">
      <div className="form-header">
        <h3>{isEditing ? 'Edit Expense' : 'Add Expense'}</h3>
        <button type="button" onClick={onCancel} className="cancel-btn">
          Cancel
        </button>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="form-group">
        <label htmlFor="group_id">Group:</label>
        <select
          id="group_id"
          name="group_id"
          value={formData.group_id}
          onChange={handleChange}
          required
          className="form-select"
        >
          <option value="">Select a group</option>
          {groups.map(group => (
            <option key={group.id} value={group.id}>
              {group.name}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="description">Description:</label>
        <input
          type="text"
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          required
          className="form-input"
          placeholder="Enter expense description"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="amount">Amount:</label>
          <input
            type="number"
            id="amount"
            name="amount"
            value={formData.amount}
            onChange={handleChange}
            required
            min="0.01"
            step="0.01"
            className="form-input"
            placeholder="Enter amount"
          />
        </div>

        <div className="form-group">
          <label htmlFor="currency">Currency:</label>
          <select
            id="currency"
            name="currency"
            value={formData.currency}
            onChange={handleChange}
            required
            className="form-select"
          >
            <option value="INR">INR (Indian Rupee)</option>
            <option value="USD">USD (US Dollar)</option>
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="exchange_rate">Exchange Rate (to INR):</label>
          <input
            type="number"
            id="exchange_rate"
            name="exchange_rate"
            value={formData.exchange_rate}
            onChange={handleChange}
            required
            min="0.0001"
            step="0.0001"
            className="form-input"
            placeholder="Enter exchange rate"
          />
        </div>

        <div className="form-group">
          <label htmlFor="date">Date:</label>
          <input
            type="date"
            id="date"
            name="date"
            value={formData.date}
            onChange={handleChange}
            required
            className="form-input"
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="split_type">Split Type:</label>
        <select
          id="split_type"
          name="split_type"
          value={formData.split_type}
          onChange={handleChange}
          required
          className="form-select"
        >
          <option value="equal">Equal Split</option>
          <option value="unequal">Unequal Split</option>
          <option value="percentage">Percentage Split</option>
          <option value="share">Share Split</option>
        </select>
      </div>

      {formData.split_type !== 'equal' && (
        <div className="form-group">
          <label htmlFor="split_details">Split Details:</label>
          <textarea
            id="split_details"
            name="split_details"
            value={formData.split_details}
            onChange={handleChange}
            rows="4"
            className="form-textarea"
            placeholder={formData.split_type === 'percentage'
              ? 'Enter as: Name X%; Name Y%; ... (must sum to 100%)'
              : formData.split_type === 'share'
                ? 'Enter as: Name X; Name Y; ... (X = number of shares)'
                : 'Enter as: Name X; Name Y; ... (X = amount)'}
          />
          <p className="form-help">Format examples above based on selected split type</p>
        </div>
      )}

      <div className="form-group">
        <label htmlFor="notes">Notes (optional):</label>
        <textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          rows="3"
          className="form-textarea"
          placeholder="Add any additional notes"
        />
      </div>

      <div className="form-group form-checkbox">
        <label>
          <input
            type="checkbox"
            id="is_settlement"
            name="is_settlement"
            checked={formData.is_settlement}
            onChange={handleChange}
          />
          This is a settlement/payment
        </label>
        <p className="form-help">Check if this expense represents a settlement/payment between users</p>
      </div>

      <div className="form-actions">
        <button
          type="submit"
          disabled={loading}
          className="submit-btn"
        >
          {loading ? 'Saving...' : (isEditing ? 'Update Expense' : 'Add Expense')}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="cancel-btn"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

export default ExpenseForm;