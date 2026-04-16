import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
    cropsApi, 
    expensesApi, 
    soilApi, 
    weatherApi, 
    dashboardApi,
    pricesApi,
    chatApi 
} from '../services/api';
import { STALE_TIME, QUERY_KEYS } from '../lib/queryClient';
import { DEFAULTS } from '../constants';

// ============================================
// WEATHER
// ============================================
export const useWeather = (city = DEFAULTS.CITY) => {
    return useQuery({
        queryKey: [QUERY_KEYS.WEATHER, city],
        queryFn: () => weatherApi.getCurrent(city),
        staleTime: STALE_TIME.SHORT,
        enabled: !!city,
    });
};

export const useWeatherForecast = (city = DEFAULTS.CITY) => {
    return useQuery({
        queryKey: [QUERY_KEYS.WEATHER_FORECAST, city],
        queryFn: () => weatherApi.getForecast(city),
        staleTime: STALE_TIME.SHORT,
        enabled: !!city,
    });
};

// ============================================
// CROPS
// ============================================
export const useCrops = () => {
    return useQuery({
        queryKey: [QUERY_KEYS.CROPS],
        queryFn: cropsApi.getAll,
        staleTime: STALE_TIME.MEDIUM,
    });
};

export const useAddCrop = () => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: cropsApi.add,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CROPS] });
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DASHBOARD] });
        },
    });
};

export const useUpdateCropStage = () => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: cropsApi.updateStage,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CROPS] });
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DASHBOARD] });
        },
    });
};

export const useDeleteCrop = () => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: cropsApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CROPS] });
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DASHBOARD] });
        },
    });
};

// ============================================
// EXPENSES
// ============================================
export const useExpenses = () => {
    return useQuery({
        queryKey: [QUERY_KEYS.EXPENSES],
        queryFn: expensesApi.getAll,
        staleTime: STALE_TIME.MEDIUM,
    });
};

export const useExpensesSummary = () => {
    return useQuery({
        queryKey: [QUERY_KEYS.EXPENSE_SUMMARY],
        queryFn: expensesApi.getSummary,
        staleTime: STALE_TIME.MEDIUM,
    });
};

export const useAddExpense = () => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: expensesApi.add,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.EXPENSES] });
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.EXPENSE_SUMMARY] });
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DASHBOARD] });
        },
    });
};

export const useDeleteExpense = () => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: expensesApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.EXPENSES] });
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.EXPENSE_SUMMARY] });
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.DASHBOARD] });
        },
    });
};

// ============================================
// SOIL
// ============================================
export const useSoilReports = () => {
    return useQuery({
        queryKey: [QUERY_KEYS.SOIL],
        queryFn: soilApi.getAll,
        staleTime: STALE_TIME.LONG,
    });
};

export const useAddSoilReport = () => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: soilApi.add,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.SOIL] });
        },
    });
};

// ============================================
// PRICES
// ============================================
export const usePrice = (crop, state) => {
    return useQuery({
        queryKey: [QUERY_KEYS.PRICES, crop, state],
        queryFn: () => pricesApi.getPrice(crop, state),
        staleTime: STALE_TIME.LONG,
        enabled: !!crop && !!state,
    });
};

// ============================================
// DASHBOARD
// ============================================
export const useDashboardInsight = (city = DEFAULTS.CITY, crop = DEFAULTS.CROP) => {
    return useQuery({
        queryKey: [QUERY_KEYS.DASHBOARD, city, crop],
        queryFn: () => dashboardApi.getInsight(city, crop),
        staleTime: STALE_TIME.SHORT,
        enabled: !!city && !!crop,
    });
};

// ============================================
// CHAT
// ============================================
export const useSendMessage = () => {
    return useMutation({
        mutationFn: chatApi.sendMessage,
    });
};
