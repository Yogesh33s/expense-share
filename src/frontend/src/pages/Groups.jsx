import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const Groups = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [groupName, setGroupName] = useState('');
  const [groupDescription, setGroupDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/groups');
      setGroups(response.data.groups);
    } catch (err) {
      setError('Failed to load groups');
      console.error('Groups fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    setError('');
    setCreating(true);

    try {
      const response = await api.post('/groups', {
        name: groupName,
        description: groupDescription
      });

      // Add the new group to the list
      setGroups(prev => [...prev, response.data.group]);

      // Reset form and close modal
      setGroupName('');
      setGroupDescription('');
      setShowCreateModal(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create group');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm('Are you sure you want to delete this group?')) {
      return;
    }

    try {
      await api.delete(`/groups/${groupId}`);
      // Remove the deleted group from the list
      setGroups(prev => prev.filter(group => group.id !== groupId));
    } catch (err) {
      setError('Failed to delete group');
      console.error('Delete group error:', err);
    }
  };

  if (loading) {
    return (
      <div className="groups-loading">
        <h2>Loading groups...</h2>
      </div>
    );
  }

  return (
    <div className="groups-page">
      <div className="groups-header">
        <h1>My Groups</h1>
        <div className="groups-actions">
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            Create Group
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Create Group Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Group</h2>
            <form onSubmit={handleCreateGroup}>
              <div className="form-group">
                <label>Group Name</label>
                <input
                  type="text"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  required
                  disabled={creating}
                />
              </div>
              <div className="form-group">
                <label>Description (optional)</label>
                <textarea
                  value={groupDescription}
                  onChange={(e) => setGroupDescription(e.target.value)}
                  disabled={creating}
                />
              </div>
              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-outline"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={creating || !groupName.trim()}
                >
                  {creating ? 'Creating...' : 'Create Group'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="groups-list">
        {groups.length === 0 ? (
          <div className="empty-state">
            <h3>No groups yet</h3>
            <p>Create your first group to get started!</p>
          </div>
        ) : (
          <div className="groups-grid">
            {groups.map(group => (
              <div key={group.id} className="group-card">
                <div className="group-header">
                  <h3>{group.name}</h3>
                  <div className="group-actions">
                    <button
                      onClick={() => navigate(`/groups/${group.id}`)}
                      className="btn btn-sm btn-outline"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleDeleteGroup(group.id)}
                      className="btn btn-sm btn-outline delete"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {group.description && (
                  <p className="group-description">{group.description}</p>
                )}
                <div className="group-footer">
                  <small>Created: {new Date(group.created_at).toLocaleDateString()}</small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Groups;