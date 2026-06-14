import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './routes/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Groups from './pages/Groups';
import GroupDetail from './pages/GroupDetail';
import Expenses from './pages/Expenses';
import Import from './pages/Import';
import ImportReportViewer from './pages/ImportReportViewer';
// import Balances from './pages/Balances';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Auth routes - no authentication required */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          /* Protected routes - require authentication */
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Navigate replace to="/dashboard" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          /* Placeholder routes for other pages */
          <Route
            path="/groups"
            element={
              <ProtectedRoute>
                <Groups />
              </ProtectedRoute>
            }
          />
          <Route
            path="/groups/:groupId"
            element={
              <ProtectedRoute>
                <GroupDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/expenses"
            element={
              <ProtectedRoute>
                <Expenses />
              </ProtectedRoute>
            }
          />
          <Route
            path="/import"
            element={
              <ProtectedRoute>
                <Import />
              </ProtectedRoute>
            }
          />
          <Route
            path="/imports/:id"
            element={
              <ProtectedRoute>
                <ImportReportViewer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/balances"
            element={
              <ProtectedRoute>
                <div>
                  <h1>Balances & Settlements</h1>
                  <p>Balances page coming soon...</p>
                </div>
              </ProtectedRoute>
            }
          />

          /* Redirect unknown routes to login */
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;