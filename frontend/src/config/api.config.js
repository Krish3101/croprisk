/**
 * API Configuration
 * Centralized API endpoints and configuration
 */

export const API_CONFIG = {
    BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    TIMEOUT: 10000,
    
    ENDPOINTS: {
        AUTH: {
            LOGIN: '/auth/login',
            REGISTER: '/auth/register',
            REFRESH: '/auth/refresh',
        },
        WEATHER: {
            CURRENT: '/weather',
            FORECAST: '/weather/forecast',
        },
        CROPS: {
            LIST: '/crops',
            ADD: '/crops/add',
            UPDATE_STAGE: '/crops/stage',
            DELETE: '/crops',
        },
        EXPENSES: {
            LIST: '/expense',
            ADD: '/expense/add',
            DELETE: '/expense',
            SUMMARY: '/expense/summary',
        },
        PRICES: '/price',
        CHATBOT: '/chatbot',
        SOIL: {
            LIST: '/soil',
            ADD: '/soil/add',
        },
        DASHBOARD: '/dashboard/insight',
    },
};

export const REQUEST_CONFIG = {
    RETRY_ATTEMPTS: 2,
    RETRY_DELAY: 1000,
};
