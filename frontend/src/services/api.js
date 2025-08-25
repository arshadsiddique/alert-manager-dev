import axios from 'axios';

let API_BASE_URL = (window.runtimeConfig && window.runtimeConfig.API_BASE_URL) || 'http://localhost:8000';

if (!API_BASE_URL.startsWith('http://localhost')) {
  // If it's a remote URL, ensure it uses https.
  // This replaces http:// with https:// if it exists.
  API_BASE_URL = API_BASE_URL.replace(/^http:\/\//i, 'https://');
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const alertsApi = {
  getAlerts: (skip = 0, limit = 5000) => 
    api.get(`/api/alerts?skip=${skip}&limit=${limit}`),
  
  getAlert: (alertId) => 
    api.get(`/api/alerts/${alertId}`),
  
  acknowledgeAlerts: (alertIds, note, acknowledgedBy) => 
    api.post('/api/alerts/acknowledge', { 
      alert_ids: alertIds, 
      note,
      acknowledged_by: acknowledgedBy || 'System User'
    }),
  
  resolveAlerts: (alertIds, note, resolvedBy) => 
    api.post('/api/alerts/resolve', { 
      alert_ids: alertIds, 
      note,
      resolved_by: resolvedBy || 'System User'
    }),
  
  syncAlerts: () => 
    api.post('/api/alerts/sync'),

  getSyncSummary: () =>
    api.get('/api/alerts/sync/summary'),
};

export const configApi = {
  getCronConfigs: () => 
    api.get('/api/config/cron'),
  
  createCronConfig: (config) => 
    api.post('/api/config/cron', config),
  
  updateCronConfig: (configId, config) => 
    api.put(`/api/config/cron/${configId}`, config),
};

export default api;
