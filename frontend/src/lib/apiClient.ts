// src/lib/apiClient.ts

import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor - Add auth token if available
apiClient.interceptors.request.use(
  (config) => {
    // You can add auth headers here when authentication is implemented
    // const token = localStorage.getItem('authToken');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      console.warn('Unauthorized - Please log in again');
    }

    // Handle 403 Forbidden
    if (error.response?.status === 403) {
      console.warn('Forbidden - You do not have permission');
    }

    // Handle 500 Server Error
    if (error.response?.status >= 500) {
      console.error('Server error - Please try again later');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
