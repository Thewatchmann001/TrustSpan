import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export const authAPI = {
  syncPrivy: (data) => api.post('/api/users/privy/sync', data),
  getCapabilities: () => api.get('/api/users/me/capabilities'),
  switchRole: (role) => api.post('/api/users/me/switch-role', { role }),
  getMe: () => api.get('/api/users/me'),
};

export const startupAPI = {
  register: (data) => api.post('/api/startups/register', data),
  update: (startupId, data) => api.put(`/api/startups/${startupId}`, data),
  addEmployee: (startupId, data) => api.post(`/api/startups/${startupId}/add-employee`, data),
  getAll: (skip = 0, limit = 100) => api.get(`/api/startups?skip=${skip}&limit=${limit}`),
  getOne: (startupId) => api.get(`/api/startups/${startupId}`),
  getStartupEmployees: (startupId) => api.get(`/api/startups/${startupId}/employees`),
  list: (params = {}) => api.get('/api/startups/list', { params }),
  verify: (startupId) => api.get(`/api/startups/verify/${startupId}`),
};

export const employerAPI = {
  apply: (data) => api.post('/api/employers/apply', data),
  getMe: () => api.get('/api/employers/me'),
  shortlist: (cvId) => api.post(`/api/employers/shortlist/${cvId}`),
  getShortlisted: () => api.get('/api/employers/shortlisted'),
};

export const adminAPI = {
  getStats: () => api.get('/api/admin/stats'),
  listEmployers: () => api.get('/api/admin/employers'),
  approveEmployer: (id) => api.patch(`/api/admin/employers/${id}/approve`),
  rejectEmployer: (id, reason) => api.patch(`/api/admin/employers/${id}/reject`, { reason }),
  listUsers: () => api.get('/api/admin/users'),
};

export const cvAPI = {
  getMe: () => api.get('/api/cv/me'),
  save: (data) => api.post('/api/cv/save', data),
  exportPDF: (data) => api.post('/api/cv/export-pdf', data, { responseType: 'blob' }),
  uploadParse: (formData) => api.post('/api/cv/upload-parse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  aiEnhance: (data) => api.post('/api/cv/ai-enhance', data),
  search: (data) => api.post('/api/cv/search', data),
};

export default api;
