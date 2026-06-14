import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const GroupDetail = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { groupId } = useParams();
  const [group, setGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [members, setMembers] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(true);

  useEffect(() => {
    fetchGroup();
    fetchGroupMembers();
  }, [groupId]);

  const fetchGroup = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get(`/groups/${groupId}`);
      setGroup(response.data.group);
      setEditName(response.data.group.name);
      setEditDescription(response.data.group.description || '');
    } catch (err) {
      setError('Failed to load group');
      console.error('Group fetch error:', err);
      navigate('/groups');
    } finally {
      setLoading(false);
    }
  };

  const fetchGroupMembers = async () => {
    setLoadingMembers(true);
    try {
      const response = await api.get(`/groups/${groupId}/users`);
      setMembers(response.data.users);
    } catch (err) {
      console.error('Fetch group members error:', err);
    } finally {
      setLoadingMembers(false);
    }
  };

  const handleUpdateGroup = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);

    try {
      const response = await api.put(`/groups/${groupId}`, {
        name: editName,
        description: editDescription
      });

      setGroup(response.data.group);
      setShowEditModal(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update group');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteGroup = async () => {
    if (!window.confirm('Are you sure you want to delete this group?')) {
      return;
    }

    try {
      await api.delete(`/groups/${groupId}`);
      navigate('/groups');
    } catch (err) {
      setError('Failed to delete group');
      console.error('Delete group error:', err);
    }
  };

  if (loading) {
    return (
      <div className="group-detail-loading">
        <h2>Loading group...</h2>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="group-detail-loading">
        <h2>Group not found</h2>
        <p>Redirecting to groups list...</p>
      </div>
    );
  }

  return (
    <div className="group-detail-page">
      <div className="group-detail-header">
        <h1>{group.name}</h1>
        <div className="group-detail-actions">
          <button
            onClick={() => setShowEditModal(true)}
            className="btn btn-sm btn-outline"
          >
            Edit
          </button>
          <button
            onClick={handleDeleteGroup}
            className="btn btn-sm btn-outline delete"
          >
            Delete
          </button>
          <button
            onClick={() => navigate('/groups')}
            className="btn btn-sm"
          >
            Back to Groups
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Edit Group Modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Edit Group</h2>
            <form onSubmit={handleUpdateGroup}>
              <div className="form-group">
                <label>Group Name</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  required
                  disabled={saving}
                />
              </div>
              <div className="form-group">
                <label>Description (optional)</label>
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  disabled={saving}
                />
              </div>
              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="btn btn-outline"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={saving || !editName.trim()}
                >
                  {saving ? 'Saving...' : 'Update Group'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="group-detail-content">
        <div className="group-info">
          <p><strong>Description:</strong> {group.description || 'No description'}</p>
          <p><strong>Created:</strong> {new Date(group.created_at).toLocaleString()}</p>
          <p><strong>Updated:</strong> {new Date(group.updated_at).toLocaleString()}</p>
          <p><strong>Created By:</strong> User ID: {group.created_by_user_id}</p>
        </div>

        <div className="group-members-section">
          <h2>Group Members ({members.length})</h2>
          {loadingMembers ? (
            <p>Loading members...</p>
          ) : (
            members.length === 0 ? (
              <p>No members in this group yet.</p>
            ) : (
              <div className="members-list">
                {members.map(member => (
                  <div key={member.id} className="member-item">
                    <div className="member-info">
                      <h3>{member.name}</h3>
                      <p>@member.email</p>
                    </div>
                    <div className="member-actions">
                      <small>Joined: {new Date(member.joined_at).toLocaleDateString()}</small>
                      {member.left_at && (
                        <span className="member-left">Left: {new Date(member.left_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};

export default GroupDetail;