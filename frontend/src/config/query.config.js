/**
 * React Query Configuration
 * Centralized query settings
 */

export const STALE_TIME = {
    SHORT: 1 * 60 * 1000,      // 1 minute
    MEDIUM: 5 * 60 * 1000,     // 5 minutes (default)
    LONG: 15 * 60 * 1000,      // 15 minutes
    VERY_LONG: 30 * 60 * 1000, // 30 minutes
};

export const QUERY_KEYS = {
    CROPS: 'crops',
    EXPENSES: 'expenses',
    EXPENSE_SUMMARY: 'expenseSummary',
    WEATHER: 'weather',
    WEATHER_FORECAST: 'weatherForecast',
    PRICES: 'prices',
    SOIL: 'soil',
    DASHBOARD: 'dashboard',
    CHAT_MESSAGES: 'chatMessages',
};

export const QUERY_CONFIG = {
    defaultOptions: {
        queries: {
            staleTime: STALE_TIME.MEDIUM,
            cacheTime: 10 * 60 * 1000,
            retry: (failureCount, error) => {
                if (error.response?.status >= 400 && error.response?.status < 500) {
                    return false;
                }
                return failureCount < 2;
            },
            refetchOnWindowFocus: import.meta.env.PROD,
            refetchOnReconnect: true,
        },
        mutations: {
            retry: 0,
        },
    },
};
