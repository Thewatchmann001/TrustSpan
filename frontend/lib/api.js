import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// API Methods
export const authAPI = {
  register: (data) => api.post('/api/users/register', data),
  login: (data) => api.post('/api/users/login', data),
  getUser: (userId) => api.get(`/api/users/${userId}`),
  syncPrivy: (data) => api.post('/api/users/privy/sync', data), // Sync Privy user with backend
  // OAuth
  initiateGoogleOAuth: (role = null) => {
    // Use the same API_BASE_URL as the axios instance
    const url = role 
      ? `/api/auth/oauth/google?role=${role}`
      : '/api/auth/oauth/google';
    // Return full URL for redirect (OAuth flow)
    return `${API_BASE_URL}${url}`;
  },
};

// Certificate API removed - not part of core solutions

export const startupAPI = {
  register: (data) => api.post('/api/startups/register', data),
  update: (startupId, data) => api.put(`/api/startups/${startupId}`, data),
  addEmployee: (startupId, data) => api.post(`/api/startups/${startupId}/add-employee`, data),
  getAll: (skip = 0, limit = 100) => api.get(`/api/startups?skip=${skip}&limit=${limit}`),
  getOne: (startupId) => api.get(`/api/startups/${startupId}`),
  getStartupEmployees: (startupId) => api.get(`/api/startups/${startupId}/employees`),
  getStartupsSeekingSkills: (userId) => api.get(`/api/startups/seeking-skills/${userId}`),
  invest: (startupId, investorId, amount) => 
    api.post(`/api/startups/${startupId}/invest?investor_id=${investorId}&amount=${amount}`),
  // New endpoints
  list: (params = {}) => api.get('/api/startups/list', { params }),
  verify: (startupId) => api.get(`/api/startups/verify/${startupId}`),
};

export const investmentAPI = {
  getUserInvestments: (userId) => api.get(`/api/investments/user/${userId}`),
  getStartupInvestments: (startupId) => api.get(`/api/investments/startup/${startupId}`),
  // New endpoints
  sendUSDC: (data) => api.post('/api/investments/usdc/send', data),
  getPortfolio: (investorId) => api.get(`/api/investments/portfolio/${investorId}`),
};

export default api;

export const jobAPI = {
  create: (data) => api.post('/api/jobs/create', data),
  getAll: (skip = 0, limit = 100) => api.get(`/api/jobs?skip=${skip}&limit=${limit}`),
  match: (userId, limit = 10, category = null, location = null) => 
    api.post('/api/jobs/match', { user_id: userId, limit, category, location }),
  apply: (userId, jobId, coverLetter = null) => 
    api.post('/api/jobs/apply', { user_id: userId, job_id: jobId, cover_letter: coverLetter }),
  getJobApplications: (jobId) => api.get(`/api/jobs/${jobId}/applications`),
  getEmployerApplications: (employerId) => api.get(`/api/jobs/employer/${employerId}/applications`),
  getUserApplications: (userId) => api.get(`/api/jobs/user/${userId}/applications`),
  getEmployerStats: (employerId) => api.get(`/api/jobs/employer/${employerId}/stats`),
  // New endpoints
  searchGlobal: (query, location = null, limit = 20) => 
    api.get('/api/jobs/search-global', { params: { query, location, limit } }),
  matchGlobal: (data) => api.post('/api/jobs/match-global', data),
};

export const cvAPI = {
  generate: (formData) => {
    return api.post('/api/cv/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getUserCV: (userId) => api.get(`/api/cv/${userId}`),
  deleteCV: (userId) => api.delete(`/api/cv/${userId}`),
  verifyCV: (cvId) => api.get(`/api/cv/verify/${cvId}`),
  getJobSeekerQR: (userId) => api.get(`/api/cv/job-seeker-qr/${userId}`),
  getMarketAnalysis: (sector) => api.get(`/api/cv/market-analysis/${sector}`),
  tailorToJob: (jobId, userId) => api.post(`/api/cv/tailor/${jobId}`, { user_id: userId }),
  enhanceLanguage: (section, content) => api.post('/api/cv/enhance-language', { section, content }),
  getRealtimeSuggestions: (section, currentText, industry) => 
    api.post('/api/cv/realtime-suggestions', { section, current_text: currentText, industry }),
  getUniversityPrompts: () => api.get('/api/cv/university-prompts'),
  calculateATSScore: (cvData) => api.post('/api/cv/ats-score', cvData, {
    headers: {
      'Content-Type': 'application/json',
    },
  }),
  getIndustryTemplate: (industry) => api.get(`/api/cv/industry-template/${industry}`),
  uploadAndParseCV: (formData) => api.post('/api/cv/upload-and-parse', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  // New endpoints
  getSuggestions: (section, content, industry = null) => 
    api.post('/api/cv/suggestions', { section, content, industry }),
  searchJobs: (keywords, jobTitles = null, location = null, limit = 50, userId = null) =>
    api.post('/api/cv/jobs', { keywords, job_titles: jobTitles, location, limit, user_id: userId }),
};

