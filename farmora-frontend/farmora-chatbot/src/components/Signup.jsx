import React, { useState } from 'react';
import { UserPlus, Mail, Lock, User, MapPin, Leaf, AlertCircle } from 'lucide-react';
import api from '../services/api';
import './Auth.css';

const Signup = ({ onSignupSuccess, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    farmLocation: '',
    crops: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Validate password length
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);

    try {
      const cropsArray = formData.crops
        .split(',')
        .map(crop => crop.trim())
        .filter(crop => crop);

      const response = await api.signup(
        formData.email,
        formData.name,
        formData.password,
        formData.farmLocation,
        cropsArray
      );

      api.setUser(response);
      onSignupSuccess(response);
    } catch (err) {
      setError(err.message || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card signup-card">
        <div className="auth-header">
          <div className="auth-logo">🌾</div>
          <h1 className="auth-title">FarMora</h1>
          <p className="auth-subtitle">Join the Smart Farming Community</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <h2 className="form-heading">Create Your Farm Account</h2>

          {error && (
            <div className="error-banner">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="name" className="form-label">Full Name</label>
              <div className="input-wrapper">
                <User className="input-icon" />
                <input
                  id="name"
                  name="name"
                  type="text"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Your name"
                  className="form-input"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="email" className="form-label">Email Address</label>
              <div className="input-wrapper">
                <Mail className="input-icon" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="your@email.com"
                  className="form-input"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <div className="input-wrapper">
                <Lock className="input-icon" />
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Min 8 characters"
                  className="form-input"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
              <div className="input-wrapper">
                <Lock className="input-icon" />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm password"
                  className="form-input"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="farmLocation" className="form-label">Farm Location</label>
              <div className="input-wrapper">
                <MapPin className="input-icon" />
                <input
                  id="farmLocation"
                  name="farmLocation"
                  type="text"
                  value={formData.farmLocation}
                  onChange={handleChange}
                  placeholder="e.g., Maharashtra, India"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="crops" className="form-label">Crops (comma-separated)</label>
              <div className="input-wrapper">
                <Leaf className="input-icon" />
                <input
                  id="crops"
                  name="crops"
                  type="text"
                  value={formData.crops}
                  onChange={handleChange}
                  placeholder="e.g., Paddy, Wheat, Corn"
                  className="form-input"
                />
              </div>
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
                Creating account...
              </>
            ) : (
              <>
                <UserPlus className="w-5 h-5" />
                Create Account
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>Already have an account?</p>
          <button
            onClick={onSwitchToLogin}
            className="switch-button"
          >
            Login here
          </button>
        </div>
      </div>
    </div>
  );
};

export default Signup;
