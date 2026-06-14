import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import './Balance.css';

const Balance = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [userBalances, setUserBalances] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [netBalance, setNetBalance] = useState(0);
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]); // Today's date in YYYY-MM-DD format

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

  // Fetch balance data when group or date changes
  useEffect(() => {
    const fetchBalanceData = async () => {
      if (!selectedGroupId) return;

      try {
        setLoading(true);
        setError('');

        // Fetch user balances
        const balancesResponse = await api.get(`/balances/${selectedGroupId}`, {
          params: { as_of_date: asOfDate }
        });
        setUserBalances(balancesResponse.data.balances || []);

        // Fetch settlement recommendations
        const settlementsResponse = await api.get(`/balances/${selectedGroupId}/settlements`, {
          params: { as_of_date: asOfDate }
        });
        setSettlements(settlementsResponse.data.settlements || []);

        // Fetch net group balance
        const netBalanceResponse = await api.get(`/balances/${selectedGroupId}/net-balance`, {
          params: { as_of_date: asOfDate }
        });
        setNetBalance(netBalanceResponse.data.net_group_balance || 0);

        setLoading(false);
      } catch (err) {
        console.error('Error fetching balance data:', err);
        setError('Failed to load balance data');
        setLoading(false);
      }
    };

    if (selectedGroupId) {
      fetchBalanceData();
    }
  }, [selectedGroupId, asOfDate]);

  const handleGroupChange = (e) => {
    const groupId = parseInt(e.target.value);
    setSelectedGroupId(groupId);
  };

  const handleDateChange = (e) => {
    setAsOfDate(e.target.value);
  };

  if (loading) {
    return <div className="balance-page">Loading...</div>;
  }

  if (error) {
    return <div className="balance-page">Error: {error}</div>;
  }

  if (!user) {
    return <div className="balance-page">Please log in to view balance information</div>;
  }

  return (
    <div className="balance-page">
      <div className="balance-header">
        <h1>Balance Dashboard</h1>
        <div className="balance-controls">
          <div className="control-group">
            <label htmlFor="group-select">Group:</label>
            <select
              id="group-select"
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
          </div>

          <div className="control-group">
            <label htmlFor="date-select">As of date:</label>
            <input
              type="date"
              id="date-select"
              value={asOfDate}
              onChange={handleDateChange}
              className="date-input"
            />
          </div>
        </div>
      </div>

      {!selectedGroupId ? (
        <div className="no-group-selected">
          <p>Please select a group to view balance information</p>
        </div>
      ) : (
        <div className="balance-content">
          {/* Summary Cards */}
          <div className="summary-cards">
            <div className="card">
              <h3>Net Group Balance</h3>
              <p className={`net-balance ${netBalance >= 0 ? 'positive' : 'negative'}`}>
                {netBalance !== 0 ? `${Math.abs(netBalance).toFixed(2)}` : '0.00'}
                <span>{netBalance >= 0 ? ' (surplus)' : ' (deficit)'}</span>
              </p>
            </div>

            <div className="card">
              <h3>Users Who Owe Money</h3>
              <p className="balance-count">
                {userBalances.filter(ub => ub.owes_money).length}
              </p>
            </div>

            <div className="card">
              <h3>Users Who Are Owed Money</h3>
              <p className="balance-count">
                {userBalances.filter(ub => ub.owed_money).length}
              </p>
            </div>

            <div className="card">
              <h3>Settlements Needed</h3>
              <p className="balance-count">{settlements.length}</p>
            </div>
          </div>

          {/* User Balances */}
          <div className="balances-section">
            <h2>User Balances</h2>
            {userBalances.length === 0 ? (
              <p className="empty-state">No balance data available for this group.</p>
            ) : (
              <div className="balances-table">
                <div className="balances-header">
                  <div>User</div>
                  <div>Balance</div>
                  <div>Status</div>
                </div>
                <div className="balances-body">
                  {userBalances.map(balance => (
                    <div key={balance.user_id} className="balance-row">
                      <div className="user-info">
                        <div>{balance.user_name}</div>
                      </div>
                      <div className={`balance-amount ${balance.balance < 0 ? 'negative' : 'positive'}`}>
                        {balance.balance >= 0 ? '+' : ''}{balance.balance.toFixed(2)}
                      </div>
                      <div className="balance-status">
                        {balance.owes_money ? (
                          <span className="status owes">Owes</span>
                        ) : balance.owed_money ? (
                          <span className="status owed">Owed</span>
                        ) : (
                          <span className="status settled">Settled</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Settlement Recommendations */}
          <div className="settlements-section">
            <h2>Settlement Recommendations</h2>
            {settlements.length === 0 ? (
              <p className="empty-state">No settlements needed. All balances are settled!</p>
            ) : (
              <div className="settlements-table">
                <div className="settlements-header">
                  <div>From (Pays)</div>
                  <div>To (Receives)</div>
                  <div>Amount</div>
                </div>
                <div className="settlements-body">
                  {settlements.map(settlement => (
                    <div key={`${settlement.from_user_id}-${settlement.to_user_id}`} className="settlement-row">
                      <div className="from-user">
                        <div>{settlement.from_user_name}</div>
                      </div>
                      <div className="to-user">
                        <div>{settlement.to_user_name}</div>
                      </div>
                      <div className="settlement-amount">
                        {settlement.amount.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Balance;