import axios from 'axios';

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const client = axios.create({
  baseURL: `${apiUrl}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.request.use(
  (config) => {
    let token = localStorage.getItem('auth_token');
    if (!token) {
      token = 'dev_token';
      localStorage.setItem('auth_token', token);
    }
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/'; 
    }
    // In a real app we'd trigger a toast notification here
    console.error('API Error:', error.response?.data?.detail || error.message);
    return Promise.reject(error);
  }
);

export default client;
