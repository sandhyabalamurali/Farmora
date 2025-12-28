import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import api from '../services/api';
import './Auth.css';

const Login = ({ onLoginSuccess, onSwitchToSignup, onClose, isModal }) => {
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
    <div className="login-page-minimal">
      {onClose && (
        <button className="auth-back-button" onClick={onClose}>
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Home</span>
        </button>
      )}
      <div className="login-container-minimal">
        <h1 className="login-heading-minimal">Login</h1>
        <form onSubmit={handleSubmit} className="login-form-minimal">
          <div className="login-form-group-minimal">
            <label htmlFor="email" className="login-label-minimal">Email Address</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email Address"
              className="login-input-minimal"
              required
              autoComplete="email"
            />
          </div>

          <div className="login-form-group-minimal">
            <label htmlFor="password" className="login-label-minimal">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="login-input-minimal"
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div className="login-error-minimal">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="login-button-minimal"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          <div className="login-footer-minimal">
            <span>Don't have an account? </span>
            <button
              type="button"
              onClick={onSwitchToSignup}
              className="login-link-minimal"
            >
              Create Account
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
