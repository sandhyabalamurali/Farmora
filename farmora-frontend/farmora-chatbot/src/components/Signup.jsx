import React, { useState, useEffect } from 'react';
import { Navigation, Loader, ArrowLeft } from 'lucide-react';
import api from '../services/api';
import './Auth.css';

const Signup = ({ onSignupSuccess, onSwitchToLogin, onClose, isModal }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    farmLocation: '',
    crops: '',
    latitude: null,
    longitude: null,
    language: 'en'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationStatus, setLocationStatus] = useState('');

  // Request GPS location on component mount
  useEffect(() => {
    requestLocation();
  }, []);

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Geolocation not supported by browser');
      return;
    }

    setLocationLoading(true);
    setLocationStatus('Requesting location permission...');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setFormData(prev => ({
          ...prev,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        }));
        setLocationStatus(`📍 Location captured: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`);
        setLocationLoading(false);
      },
      (error) => {
        console.error('Geolocation error:', error);
        switch(error.code) {
          case error.PERMISSION_DENIED:
            setLocationStatus('❌ Location permission denied. Weather features will be limited.');
            break;
          case error.POSITION_UNAVAILABLE:
            setLocationStatus('❌ Location unavailable. Please try again.');
            break;
          case error.TIMEOUT:
            setLocationStatus('❌ Location request timed out.');
            break;
          default:
            setLocationStatus('❌ Unable to get location.');
        }
        setLocationLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  };

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

    // Warn if no location
    if (!formData.latitude || !formData.longitude) {
      const proceed = window.confirm('Location not captured. Weather features will be limited. Continue anyway?');
      if (!proceed) return;
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
        cropsArray,
        formData.latitude,
        formData.longitude,
        formData.language
      );

      api.setUser(response);
      onSignupSuccess(response);
    } catch (err) {
      setError(err.message || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'हिंदी (Hindi)' },
    { code: 'bn', name: 'বাংলা (Bengali)' },
    { code: 'gu', name: 'ગુજરાતી (Gujarati)' },
    { code: 'kn', name: 'ಕನ್ನಡ (Kannada)' },
    { code: 'ml', name: 'മലയാളം (Malayalam)' },
    { code: 'mr', name: 'मराठी (Marathi)' },
    { code: 'ta', name: 'தமிழ் (Tamil)' },
    { code: 'te', name: 'తెలుగు (Telugu)' },
    { code: 'ur', name: 'اردو (Urdu)' }
  ];

  return (
    <div className="signup-page-minimal">
      {onClose && (
        <button className="auth-back-button" onClick={onClose}>
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Home</span>
        </button>
      )}
      <div className="signup-container-minimal">
        {/* <br></br>
        <br></br>
        <br></br> */}
        <h1 className="signup-heading-minimal">Signup</h1>
        <form onSubmit={handleSubmit} className="signup-form-minimal">
          {error && (
            <div className="signup-error-minimal">{error}</div>
          )}

          {/* Location Status */}
          <div className="signup-location-minimal">
            {locationLoading ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <Navigation className="w-4 h-4" />
            )}
            <span>{locationStatus || 'Click to capture your location'}</span>
            {!formData.latitude && !locationLoading && (
              <button 
                type="button" 
                onClick={requestLocation}
                className="signup-retry-minimal"
              >
                Retry
              </button>
            )}
          </div>

          <div className="signup-form-row-minimal">
            <div className="signup-form-group-minimal">
              <label htmlFor="name" className="signup-label-minimal">Full Name</label>
              <input
                id="name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleChange}
                placeholder="Full Name"
                className="signup-input-minimal"
                required
              />
            </div>

            <div className="signup-form-group-minimal">
              <label htmlFor="email" className="signup-label-minimal">Email Address</label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Email Address"
                className="signup-input-minimal"
                required
              />
            </div>
          </div>

          <div className="signup-form-row-minimal">
            <div className="signup-form-group-minimal">
              <label htmlFor="password" className="signup-label-minimal">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Password"
                className="signup-input-minimal"
                required
              />
            </div>

            <div className="signup-form-group-minimal">
              <label htmlFor="confirmPassword" className="signup-label-minimal">Confirm Password</label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Confirm Password"
                className="signup-input-minimal"
                required
              />
            </div>
          </div>

          <div className="signup-form-row-minimal">
            <div className="signup-form-group-minimal">
              <label htmlFor="farmLocation" className="signup-label-minimal">Farm Location</label>
              <input
                id="farmLocation"
                name="farmLocation"
                type="text"
                value={formData.farmLocation}
                onChange={handleChange}
                placeholder="Farm Location"
                className="signup-input-minimal"
              />
            </div>

            <div className="signup-form-group-minimal">
              <label htmlFor="crops" className="signup-label-minimal">Crops (comma-separated)</label>
              <input
                id="crops"
                name="crops"
                type="text"
                value={formData.crops}
                onChange={handleChange}
                placeholder="Crops"
                className="signup-input-minimal"
              />
            </div>
          </div>

          <div className="signup-form-group-minimal">
            <label htmlFor="language" className="signup-label-minimal">Preferred Language</label>
            <select
              id="language"
              name="language"
              value={formData.language}
              onChange={handleChange}
              className="signup-input-minimal"
            >
              {languages.map(lang => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="signup-button-minimal"
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>

          <div className="signup-footer-minimal">
            <span>Already have an account? </span>
            <button
              type="button"
              onClick={onSwitchToLogin}
              className="signup-link-minimal"
            >
              Login
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Signup;
