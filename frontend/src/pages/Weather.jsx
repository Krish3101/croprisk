import { useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Cloud, CloudSun, Droplets, Loader, MapPin, Search, Wind } from 'lucide-react';

import PageTransition from '../components/PageTransition';
import { SkeletonCard } from '../components/SkeletonLoader';
import { useWeather, useWeatherForecast } from '../hooks/useApi';

const Weather = () => {
    const [city, setCity] = useState('Pune');
    const [searchQuery, setSearchQuery] = useState('');

    // Use React Query hooks with automatic caching
    const { data: weather, isLoading: loading, isError, error: queryError } = useWeather(city);
    const { data: forecastData, isLoading: forecastLoading } = useWeatherForecast(city);
    
    const error = isError ? (queryError?.message || 'Failed to fetch weather data') : null;

    // Helper to format date
    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        if (date.toDateString() === today.toDateString()) return 'Today';
        if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
        
        return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    };

    const handleSearch = (e) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            setCity(searchQuery.trim());
            setSearchQuery('');
        }
    };

    return (
        <PageTransition>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-gray-900">Weather Forecast</h1>

                    <form onSubmit={handleSearch} className="flex gap-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search city..."
                                className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                            />
                        </div>
                        <button
                            type="submit"
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        >
                            Search
                        </button>
                    </form>
                </div>

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <Loader className="w-8 h-8 text-green-600 animate-spin" />
                    </div>
                ) : error ? (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-red-50 text-red-600 p-4 rounded-lg border border-red-100"
                    >
                        {error}
                    </motion.div>
                ) : weather ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Main Weather Card */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-8 text-white shadow-lg"
                        >
                            <div className="flex items-center justify-between mb-8">
                                <div className="flex items-center gap-2">
                                    <MapPin className="w-6 h-6" />
                                    <span className="text-xl font-medium">{weather.city}</span>
                                </div>
                                <span className="text-blue-100 bg-white/20 px-3 py-1 rounded-full text-sm">
                                    Today
                                </span>
                            </div>

                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="text-6xl font-bold mb-2">{Math.round(weather.temperature)}°C</div>
                                    <div className="text-xl text-blue-100 capitalize">{weather.condition}</div>
                                </div>
                                <Cloud className="w-24 h-24 text-blue-100 opacity-80" />
                            </div>
                        </motion.div>

                        {/* Details Grid */}
                        <div className="grid grid-cols-2 gap-4">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center gap-3"
                            >
                                <div className="p-3 bg-blue-50 rounded-full text-blue-600">
                                    <Droplets className="w-6 h-6" />
                                </div>
                                <div className="text-center">
                                    <div className="text-sm text-gray-500">Humidity</div>
                                    <div className="text-xl font-semibold text-gray-900">{weather.humidity}%</div>
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                                className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center gap-3"
                            >
                                <div className="p-3 bg-gray-50 rounded-full text-gray-600">
                                    <Wind className="w-6 h-6" />
                                </div>
                                <div className="text-center">
                                    <div className="text-sm text-gray-500">Wind Speed</div>
                                    <div className="text-xl font-semibold text-gray-900">{weather.wind_speed} km/h</div>
                                </div>
                            </motion.div>
                        </div>
                    </div>
                ) : null}

                {/* 5-Day Forecast */}
                <div className="mt-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Calendar className="w-5 h-5 text-gray-600" />
                        <h2 className="text-xl font-semibold text-gray-900">5-Day Forecast</h2>
                    </div>
                    
                    {forecastLoading ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                            {[...Array(5)].map((_, i) => (
                                <SkeletonCard key={i} />
                            ))}
                        </div>
                    ) : forecastData?.forecast ? (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4"
                        >
                            {forecastData.forecast.map((day, index) => (
                                <motion.div
                                    key={day.date}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.5 + index * 0.1 }}
                                    className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-all hover:scale-105"
                                >
                                    <div className="text-center">
                                        <div className="text-sm font-medium text-gray-900 mb-2">
                                            {formatDate(day.date)}
                                        </div>
                                        <div className="flex justify-center mb-3">
                                            <CloudSun className="w-12 h-12 text-blue-400" />
                                        </div>
                                        <div className="text-3xl font-bold text-gray-900 mb-1">
                                            {Math.round(day.temp)}°C
                                        </div>
                                        <div className="text-xs text-gray-500 mb-2">
                                            {Math.round(day.temp_min)}° / {Math.round(day.temp_max)}°
                                        </div>
                                        <div className="text-sm text-gray-600 capitalize line-clamp-2">
                                            {day.condition}
                                        </div>
                                        <div className="mt-3 pt-3 border-t border-gray-100">
                                            <div className="flex items-center justify-center gap-1 text-xs text-gray-500">
                                                <Droplets className="w-3 h-3" />
                                                {Math.round(day.humidity)}%
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </motion.div>
                    ) : (
                        <div className="bg-gray-50 text-gray-500 p-8 rounded-xl text-center">
                            Forecast data unavailable
                        </div>
                    )}
                </div>
            </div>
        </PageTransition>
    );
};

export default Weather;
