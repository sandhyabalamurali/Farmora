import React, { useState } from 'react';
import { LogIn, Mail, Lock, AlertCircle } from 'lucide-react';
import api from '../services/api';
import './Auth.css';

const Login = ({ onLoginSuccess, onSwitchToSignup }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.login(email, password);
      api.setUser(response);
      onLoginSuccess(response);
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">🌾</div>
          <h1 className="auth-title">FarMora</h1>
          <p className="auth-subtitle">Smart Farming Assistant</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <h2 className="form-heading">Welcome Back, Farmer!</h2>

          {error && (
            <div className="error-banner">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email" className="form-label">Email Address</label>
            <div className="input-wrapper">
              <Mail className="input-icon" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="form-input"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <div className="input-wrapper">
              <Lock className="input-icon" />
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="form-input"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="submit-button"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Logging in...
              </>
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                Login
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>Don't have an account?</p>
          <button
            onClick={onSwitchToSignup}
            className="switch-button"
          >
            Create one here
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
