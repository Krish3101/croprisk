import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, ArrowRight, CloudRain, CloudSun, IndianRupee, Lightbulb, Sprout, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';

import EmptyState from '../components/EmptyState';
import InsightReport from '../components/InsightReport';
import PageTransition from '../components/PageTransition';
import { SkeletonCard, SkeletonDashboard } from '../components/SkeletonLoader';
import { DEFAULTS } from '../constants';
import { useAuth } from '../hooks/useAuth';
import { useCrops, useDashboardInsight, useExpensesSummary, useWeather } from '../hooks/useApi';

const DEFAULT_INSIGHT_CROP = 'Tomato';
const MAX_CROPS_TO_DISPLAY = 3;

const Dashboard = () => {
    const { user } = useAuth();
    
    // Use React Query hooks for data fetching
    const { data: weather, isLoading: weatherLoading } = useWeather(DEFAULTS.CITY);
    const { data: crops = [], isLoading: cropsLoading } = useCrops();
    const { data: finance, isLoading: financeLoading } = useExpensesSummary();
    const { data: insightData, isLoading: insightLoading, isError: insightError } = useDashboardInsight(DEFAULTS.CITY, DEFAULT_INSIGHT_CROP);
    
    const loading = weatherLoading || cropsLoading || financeLoading;

    // Memoize animation variants
    const container = useMemo(() => ({
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    }), []);

    const item = useMemo(() => ({
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 }
    }), []);

    if (loading) {
        return (
            <PageTransition>
                <SkeletonDashboard />
            </PageTransition>
        );
    }

    return (
        <PageTransition>
            <div className="space-y-8">
                {/* Welcome Section */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gradient-to-r from-green-600 to-green-700 rounded-2xl p-8 text-white shadow-lg relative overflow-hidden"
                >
                    <div className="relative z-10">
                        <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.full_name || user?.username}!</h1>
                        <p className="text-green-100">Here&apos;s what&apos;s happening on your farm today.</p>
                    </div>
                    <div className="absolute right-0 top-0 h-full w-1/3 bg-white/5 skew-x-12 transform translate-x-12"></div>
                </motion.div>

                <motion.div
                    variants={container}
                    initial="hidden"
                    animate="show"
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                >
                    {/* Weather Widget */}
                    <motion.div variants={item} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow group">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-gray-900">Weather</h3>
                            <div className="p-2 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                                <CloudSun className="w-5 h-5 text-blue-500" />
                            </div>
                        </div>
                        {weather && !weather.error ? (
                            <div>
                                <div className="flex items-end gap-2 mb-2">
                                    <span className="text-4xl font-bold text-gray-900">
                                        {Math.round(weather.temp || weather.temperature || 0)}°C
                                    </span>
                                    <span className="text-gray-500 mb-1">{weather.city || 'Unknown'}</span>
                                </div>
                                <p className="text-gray-600 capitalize">
                                    {weather.condition || weather.weather || 'N/A'}
                                </p>
                                <div className="mt-4 flex gap-4 text-sm text-gray-500">
                                    <span>Humidity: {weather.humidity || 0}%</span>
                                    <span>Wind: {weather.wind_speed || 0} km/h</span>
                                </div>
                            </div>
                        ) : (
                            <p className="text-gray-500">Weather data unavailable</p>
                        )}
                        <Link to="/weather" className="mt-4 inline-flex items-center text-sm text-green-600 hover:text-green-700 font-medium group-hover:translate-x-1 transition-transform">
                            View Forecast <ArrowRight className="w-4 h-4 ml-1" />
                        </Link>
                    </motion.div>

                    {/* Crops Widget */}
                    <motion.div variants={item} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow group">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-gray-900">Active Crops</h3>
                            <div className="p-2 bg-green-50 rounded-lg group-hover:bg-green-100 transition-colors">
                                <Sprout className="w-5 h-5 text-green-500" />
                            </div>
                        </div>
                        <div className="space-y-3">
                            {crops.slice(0, MAX_CROPS_TO_DISPLAY).map((crop) => (
                                <div key={crop.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                                    <div>
                                        <div className="font-medium text-gray-900">{crop.crop}</div>
                                        <div className="text-xs text-gray-500">{crop.plot}</div>
                                    </div>
                                    <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                                        {crop.stage}
                                    </span>
                                </div>
                            ))}
                            {crops.length === 0 && <p className="text-gray-500">No active crops</p>}
                        </div>
                        <Link to="/crops" className="mt-4 inline-flex items-center text-sm text-green-600 hover:text-green-700 font-medium group-hover:translate-x-1 transition-transform">
                            Manage Crops <ArrowRight className="w-4 h-4 ml-1" />
                        </Link>
                    </motion.div>

                    {/* Finance Widget */}
                    <motion.div variants={item} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow group">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-gray-900">Finances</h3>
                            <div className="p-2 bg-yellow-50 rounded-lg group-hover:bg-yellow-100 transition-colors">
                                <IndianRupee className="w-5 h-5 text-yellow-500" />
                            </div>
                        </div>
                        {finance && !finance.error ? (
                            <div className="space-y-4">
                                <div>
                                    <div className="text-sm text-gray-500">Net Profit</div>
                                    <div className={`text-2xl font-bold ${(finance.profit || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        ₹{(finance.profit || 0).toLocaleString()}
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-2 bg-green-50 rounded-lg">
                                        <div className="text-xs text-green-600 mb-1 flex items-center gap-1">
                                            <TrendingUp className="w-3 h-3" /> Income
                                        </div>
                                        <div className="font-semibold text-gray-900">₹{(finance.total_income || 0).toLocaleString()}</div>
                                    </div>
                                    <div className="p-2 bg-red-50 rounded-lg">
                                        <div className="text-xs text-red-600 mb-1 flex items-center gap-1">
                                            <TrendingUp className="w-3 h-3 rotate-180" /> Expense
                                        </div>
                                        <div className="font-semibold text-gray-900">₹{(finance.total_expense || 0).toLocaleString()}</div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <p className="text-gray-500">Financial data unavailable</p>
                        )}
                        <Link to="/finances" className="mt-4 inline-flex items-center text-sm text-green-600 hover:text-green-700 font-medium group-hover:translate-x-1 transition-transform">
                            View Details <ArrowRight className="w-4 h-4 ml-1" />
                        </Link>
                    </motion.div>

                    {/* AI Insights Widget */}
                    <motion.div variants={item} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow group lg:col-span-3">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-gray-900">AI Insights</h3>
                            <div className="p-2 bg-purple-50 rounded-lg group-hover:bg-purple-100 transition-colors">
                                <Lightbulb className="w-5 h-5 text-purple-500" />
                            </div>
                        </div>
                        {insightLoading ? (
                            <SkeletonCard />
                        ) : insightError ? (
                            <EmptyState
                                icon={AlertCircle}
                                title="Unable to load insights"
                                description="AI insights are temporarily unavailable. Please try again later."
                            />
                        ) : insightData?.insight ? (
                            <div className="space-y-4">
                                <InsightReport insight={insightData.insight} />
                            </div>
                        ) : (
                            <EmptyState
                                icon={Lightbulb}
                                title="No insights available"
                                description="AI insights will appear here based on your farm data."
                            />
                        )}
                    </motion.div>
                </motion.div>
            </div>
        </PageTransition>
    );
};

export default Dashboard;
