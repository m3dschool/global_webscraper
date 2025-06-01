import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/auth/token', formData);
  },
  register: (userData) => api.post('/auth/register', userData),
};

// Configs API
export const configsApi = {
  getAll: (skip = 0, limit = 100) => 
    api.get(`/configs?skip=${skip}&limit=${limit}`),
  getById: (id) => api.get(`/configs/${id}`),
  create: (data) => api.post('/configs', data),
  update: (id, data) => api.put(`/configs/${id}`, data),
  delete: (id) => api.delete(`/configs/${id}`),
};

// Results API
export const resultsApi = {
  getAll: (page = 1, size = 50, configId = null, status = null) => {
    const params = new URLSearchParams({ page: page.toString(), size: size.toString() });
    if (configId) params.append('config_id', configId.toString());
    if (status) params.append('status_filter', status);
    return api.get(`/results?${params}`);
  },
  getById: (id) => api.get(`/results/${id}`),
  getRawHtml: (id) => api.get(`/results/${id}/raw-html`),
};

// Jobs API
export const jobsApi = {
  trigger: (configId) => api.post('/jobs/trigger', { config_id: configId }),
  getStatus: (configId) => api.get(`/jobs/status/${configId}`),
  getTaskStatus: (taskId) => api.get(`/jobs/task/${taskId}`),
};

export default api;