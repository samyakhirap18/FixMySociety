import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

api.interceptors.request.use((config) => {
  const publicEndpoint = [
    '/auth/login/',
    '/auth/register/',
    '/auth/logout/',
    '/auth/token/refresh/',
  ].some((path) => config.url?.includes(path));
  if (publicEndpoint) {
    delete config.headers.Authorization;
    return config;
  }
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshRequest;
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config;
    const isAuthRequest = request?.url?.includes('/auth/login/');
    if (error.response?.status !== 401 || !request || request._retried || isAuthRequest) {
      return Promise.reject(error);
    }

    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return Promise.reject(error);
    request._retried = true;

    try {
      if (!refreshRequest) {
        refreshRequest = axios.post(
          `${api.defaults.baseURL}/auth/token/refresh/`,
          { refresh },
        ).finally(() => { refreshRequest = null; });
      }
      const response = await refreshRequest;
      localStorage.setItem('access_token', response.data.access);
      if (response.data.refresh) {
        localStorage.setItem('refresh_token', response.data.refresh);
      }
      request.headers.Authorization = `Bearer ${response.data.access}`;
      return api(request);
    } catch (refreshError) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      return Promise.reject(refreshError);
    }
  },
);

export const authAPI = {
  register: (data) => api.post('/auth/register/', data),
  login: (email, password) => api.post('/auth/login/', { email, password }),
  logout: () => api.post('/auth/logout/', { refresh: localStorage.getItem('refresh_token') }),
  me: () => api.get('/auth/users/me/'),
};

export const societyAPI = { list: () => api.get('/societies/') };
export const categoryAPI = { list: () => api.get('/categories/') };
export const complaintAPI = {
  list: () => api.get('/complaints/'),
  create: (data) => api.post('/complaints/', data),
  upvote: (id) => api.post(`/complaints/${id}/upvote/`),
  status: (id, status) => api.patch(`/complaints/${id}/status/`, { status }),
  assign: (id, assigned_to) => api.patch(`/complaints/${id}/assign/`, { assigned_to }),
  priority: (id, priority) => api.patch(`/complaints/${id}/priority/`, { priority }),
  dashboard: () => api.get('/dashboard/'),
};
export const workerAPI = {
  list: () => api.get('/workers/'),
  create: (data) => api.post('/workers/', data),
};
export default api;
