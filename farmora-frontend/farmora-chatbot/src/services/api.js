/**
 * API Service - Handles all backend communication
 * Base URL from environment variable
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL 
  ? `${import.meta.env.VITE_API_BASE_URL}/api` 
  : 'http://localhost:8000/api';

class APIService {
  constructor() {
    this.token = localStorage.getItem('farmora_token');
  }

  // ===== AUTH ENDPOINTS =====
  
  async signup(email, name, password, farmLocation = '', crops = []) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          name,
          password,
          farm_location: farmLocation,
          crops: crops.length > 0 ? crops : undefined
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Signup failed');
      }

      const data = await response.json();
      this.setToken(data.access_token);
      return data;
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    }
  }

  async login(email, password) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      this.setToken(data.access_token);
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async getUserProfile() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) throw new Error('Failed to fetch profile');
      return await response.json();
    } catch (error) {
      console.error('Profile fetch error:', error);
      throw error;
    }
  }

  // ===== CHAT ENDPOINT =====
  
  async sendMessage(userId, textMessage, cropImage = null, caption = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          user_id: userId,
          text_message: textMessage,
          crop_image: cropImage,
          caption: caption
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Message failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Chat error:', error);
      throw error;
    }
  }

  // ===== TASK ENDPOINTS =====
  
  async confirmTask(taskId, userId, confirmation) {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/confirm`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          task_id: taskId,
          user_id: userId,
          confirmation
        })
      });

      if (!response.ok) throw new Error('Confirmation failed');
      return await response.json();
    } catch (error) {
      console.error('Task confirmation error:', error);
      throw error;
    }
  }

  async completeTask(taskId, userId) {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ user_id: userId })
      });

      if (!response.ok) throw new Error('Completion failed');
      return await response.json();
    } catch (error) {
      console.error('Task completion error:', error);
      throw error;
    }
  }

  async getUserTasks(userId, status = null) {
    try {
      const url = new URL(`${API_BASE_URL}/tasks/${userId}`);
      if (status) url.searchParams.append('status', status);

      const response = await fetch(url.toString(), {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) throw new Error('Failed to fetch tasks');
      return await response.json();
    } catch (error) {
      console.error('Fetch tasks error:', error);
      throw error;
    }
  }

  async getTimeline(userId) {
    try {
      const response = await fetch(`${API_BASE_URL}/timeline/${userId}`, {
        headers: this.getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch timeline');
      return await response.json();
    } catch (error) {
      console.error('Fetch timeline error:', error);
      throw error;
    }
  }

  async getMarketData(userId) {
    try {
      const response = await fetch(`${API_BASE_URL}/market/${userId}`, {
        headers: this.getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch market data');
      return await response.json();
    } catch (error) {
      console.error('Fetch market data error:', error);
      throw error;
    }
  }

  // ===== HEALTH CHECK =====
  
  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return await response.json();
    } catch (error) {
      console.error('Health check error:', error);
      return { status: 'unhealthy' };
    }
  }

  // ===== UTILITY METHODS =====
  
  setToken(token) {
    this.token = token;
    localStorage.setItem('farmora_token', token);
  }

  getToken() {
    return this.token || localStorage.getItem('farmora_token');
  }

  logout() {
    this.token = null;
    localStorage.removeItem('farmora_token');
    localStorage.removeItem('farmora_user');
  }

  isAuthenticated() {
    return !!this.getToken();
  }

  getAuthHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getToken()}`
    };
  }

  setUser(user) {
    localStorage.setItem('farmora_user', JSON.stringify(user));
  }

  getUser() {
    const user = localStorage.getItem('farmora_user');
    return user ? JSON.parse(user) : null;
  }
}

export default new APIService();
