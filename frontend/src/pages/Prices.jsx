import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, MapPin, Search } from 'lucide-react';

import PageTransition from '../components/PageTransition';
import { DEFAULTS, INDIAN_STATES } from '../constants';
import { usePrice } from '../hooks/useApi';
import { formatDate } from '../utils/dateUtils';

const Prices = () => {
    const [searchParams, setSearchParams] = useState({ crop: DEFAULTS.CROP, state: DEFAULTS.STATE });
    const [submittedParams, setSubmittedParams] = useState({ crop: DEFAULTS.CROP, state: DEFAULTS.STATE });

    // Use React Query hook - only fetch when params are submitted
    const { data: priceData, isLoading: loading, isError, error: queryError } = usePrice(
        submittedParams.crop,
        submittedParams.state
    );

    const error = isError ? (queryError?.message || 'Failed to fetch price data') : null;

    const handleSearch = useCallback((e) => {
        e.preventDefault();
        setSubmittedParams({ ...searchParams });
    }, [searchParams]);

    return (
        <PageTransition>
            <div className="space-y-6">
                <h1 className="text-2xl font-bold text-gray-900">Market Prices (Mandi)</h1>

                {/* Search Form */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label htmlFor="crop" className="block text-sm font-medium text-gray-700 mb-1">
                                Crop
                            </label>
                            <input
                                id="crop"
                                type="text"
                                value={searchParams.crop}
                                onChange={(e) => setSearchParams({ ...searchParams, crop: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                                placeholder="e.g. Wheat, Rice, Onion"
                                autoComplete="off"
                            />
                        </div>
                        <div>
                            <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
                                State
                            </label>
                            <select
                                id="state"
                                value={searchParams.state}
                                onChange={(e) => setSearchParams({ ...searchParams, state: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                            >
                                {INDIAN_STATES.map((state) => (
                                    <option key={state} value={state}>
                                        {state}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="flex items-end">
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                                aria-label="Check price"
                            >
                                <Search className="w-4 h-4" />
                                {loading ? 'Searching...' : 'Check Price'}
                            </button>
                        </div>
                    </form>
                </div>

                {/* Results */}
                {error ? (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-red-50 text-red-600 p-4 rounded-lg border border-red-100"
                    >
                        {error}
                    </motion.div>
                ) : priceData ? (
                    <div className="space-y-6">
                        {/* Main Price Card */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-white p-6 rounded-xl shadow-sm border border-gray-100"
                        >
                            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">{priceData.crop}</h2>
                                    <div className="flex items-center gap-2 text-gray-500 mt-1">
                                        <MapPin className="w-4 h-4" />
                                        <span>{priceData.market}, {priceData.district}, {priceData.state}</span>
                                    </div>
                                </div>
                                <div className="mt-4 md:mt-0 text-right">
                                    <div className="text-sm text-gray-500">Modal Price</div>
                                    <div className="text-3xl font-bold text-green-600">₹{priceData?.modal_price || 'N/A'}</div>
                                    <div className="text-sm text-gray-500">per {priceData?.unit || 'Quintal'}</div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-gray-100">
                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <div className="text-sm text-gray-500 mb-1">Minimum Price</div>
                                    <div className="text-xl font-semibold text-gray-900">₹{priceData?.min_price || 'N/A'}</div>
                                </div>
                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <div className="text-sm text-gray-500 mb-1">Maximum Price</div>
                                    <div className="text-xl font-semibold text-gray-900">₹{priceData?.max_price || 'N/A'}</div>
                                </div>
                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <div className="text-sm text-gray-500 mb-1">Arrival Date</div>
                                    <div className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                                        <Calendar className="w-4 h-4" />
                                        {formatDate(priceData?.arrival_date)}
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Price History (Simulated) */}
                        {priceData.history && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="bg-white p-6 rounded-xl shadow-sm border border-gray-100"
                            >
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Price Trend (Last 7 Days)</h3>
                                <div className="h-48 flex items-end justify-between gap-2">
                                    {priceData.history.map((point, index) => {
                                        const maxVal = Math.max(...priceData.history.map(p => p.price));
                                        const height = (point.price / maxVal) * 100;

                                        return (
                                            <div key={index} className="flex-1 flex flex-col items-center gap-2 group">
                                                <div className="relative w-full flex justify-center">
                                                    <motion.div
                                                        initial={{ height: 0 }}
                                                        animate={{ height: `${height}%` }}
                                                        transition={{ duration: 0.5, delay: index * 0.1 }}
                                                        className="w-full max-w-[2rem] bg-green-100 hover:bg-green-200 rounded-t-lg transition-colors relative group-hover:bg-green-300"
                                                    >
                                                        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                                            ₹{point.price}
                                                        </div>
                                                    </motion.div>
                                                </div>
                                                <span className="text-xs text-gray-500">{point.date}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </motion.div>
                        )}
                    </div>
                ) : null}
            </div>
        </PageTransition>
    );
};

export default Prices;
