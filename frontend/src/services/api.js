import axios from 'axios';
import { API_CONFIG } from '../config/api.config';

// Create axios instance
const api = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: API_CONFIG.TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
    (response) => response.data,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// API Services
export const authApi = {
    login: (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        return api.post(API_CONFIG.ENDPOINTS.AUTH.LOGIN, formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    },
    register: (data) => api.post(API_CONFIG.ENDPOINTS.AUTH.REGISTER, data),
};

export const weatherApi = {
    getCurrent: (city) => api.get(`${API_CONFIG.ENDPOINTS.WEATHER.CURRENT}?city=${city}`),
    getForecast: (city) => api.get(`${API_CONFIG.ENDPOINTS.WEATHER.FORECAST}?city=${city}`),
};

export const cropsApi = {
    getAll: () => api.get(API_CONFIG.ENDPOINTS.CROPS.LIST),
    add: (data) => api.post(API_CONFIG.ENDPOINTS.CROPS.ADD, data),
    updateStage: ({ cropId, stage }) => 
        api.put(`${API_CONFIG.ENDPOINTS.CROPS.UPDATE_STAGE}/${cropId}`, { stage }),
    delete: (cropId) => api.delete(`${API_CONFIG.ENDPOINTS.CROPS.DELETE}/${cropId}`),
};

export const expensesApi = {
    getAll: () => api.get(API_CONFIG.ENDPOINTS.EXPENSES.LIST),
    add: (data) => api.post(API_CONFIG.ENDPOINTS.EXPENSES.ADD, data),
    delete: (expenseId) => api.delete(`${API_CONFIG.ENDPOINTS.EXPENSES.DELETE}/${expenseId}`),
    getSummary: () => api.get(API_CONFIG.ENDPOINTS.EXPENSES.SUMMARY),
};

export const pricesApi = {
    getPrice: (crop, state) => api.get(`${API_CONFIG.ENDPOINTS.PRICES}?crop=${crop}&state=${state}`),
};

export const chatApi = {
    sendMessage: (data) => api.post(API_CONFIG.ENDPOINTS.CHATBOT, data),
};

export const soilApi = {
    getAll: () => api.get(API_CONFIG.ENDPOINTS.SOIL.LIST),
    add: (data) => api.post(API_CONFIG.ENDPOINTS.SOIL.ADD, data),
};

export const dashboardApi = {
    getInsight: (city, crop) => 
        api.get(`${API_CONFIG.ENDPOINTS.DASHBOARD}?city=${city}&crop=${crop}`),
};

export default api;
