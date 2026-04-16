import { useCallback, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Droplets, Leaf, Plus, TestTube } from 'lucide-react';

import EmptyState from '../components/EmptyState';
import Modal from '../components/Modal';
import PageTransition from '../components/PageTransition';
import { SkeletonList } from '../components/SkeletonLoader';
import { useAddSoilReport, useSoilReports } from '../hooks/useApi';

const Soil = () => {
    const [showAddModal, setShowAddModal] = useState(false);
    const [newReport, setNewReport] = useState({
        nitrogen: '',
        phosphorus: '',
        potassium: '',
        ph: '',
        moisture: '',
        location: ''
    });

    // Use React Query hooks
    const { data: reports = [], isLoading: loading } = useSoilReports();
    const addReportMutation = useAddSoilReport();

    const handleAddReport = useCallback(async (e) => {
        e.preventDefault();
        try {
            await addReportMutation.mutateAsync({
                ...newReport,
                nitrogen: parseFloat(newReport.nitrogen),
                phosphorus: parseFloat(newReport.phosphorus),
                potassium: parseFloat(newReport.potassium),
                ph: parseFloat(newReport.ph),
                moisture: parseFloat(newReport.moisture)
            });
            setShowAddModal(false);
            setNewReport({
                nitrogen: '',
                phosphorus: '',
                potassium: '',
                ph: '',
                moisture: '',
                location: ''
            });
        } catch (error) {
            // Error already handled by mutation
        }
    }, [addReportMutation, newReport]);

    // Helper function to get pH status
    const getPhStatus = (ph) => {
        if (ph < 6.0) return { label: 'Acidic', color: 'text-orange-600 bg-orange-50' };
        if (ph > 7.5) return { label: 'Alkaline', color: 'text-purple-600 bg-purple-50' };
        return { label: 'Neutral', color: 'text-green-600 bg-green-50' };
    };

    // Helper function to get moisture status
    const getMoistureStatus = (moisture) => {
        if (moisture < 20) return { label: 'Low', color: 'text-red-600 bg-red-50' };
        if (moisture > 60) return { label: 'High', color: 'text-blue-600 bg-blue-50' };
        return { label: 'Optimal', color: 'text-green-600 bg-green-50' };
    };

    // Helper function to get NPK status
    const getNPKStatus = (value) => {
        if (value < 20) return { label: 'Low', color: 'text-red-600' };
        if (value > 50) return { label: 'High', color: 'text-green-600' };
        return { label: 'Medium', color: 'text-yellow-600' };
    };

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

    return (
        <PageTransition>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-gray-900">Soil Analysis</h1>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        aria-label="Add new soil report"
                    >
                        <Plus className="w-4 h-4" />
                        Add Report
                    </button>
                </div>

                {loading ? (
                    <SkeletonList count={6} />
                ) : reports.length === 0 ? (
                    <EmptyState
                        icon={Leaf}
                        title="No soil reports found"
                        description="Start by adding your first soil analysis report to track soil health."
                        action={() => setShowAddModal(true)}
                        actionLabel="Add Your First Report"
                    />
                ) : (
                    <motion.div
                        variants={container}
                        initial="hidden"
                        animate="show"
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                    >
                        {reports.map((report) => {
                            const phStatus = getPhStatus(report.ph);
                            const moistureStatus = getMoistureStatus(report.moisture);
                            const nStatus = getNPKStatus(report.nitrogen);
                            const pStatus = getNPKStatus(report.phosphorus);
                            const kStatus = getNPKStatus(report.potassium);

                            return (
                                <motion.div
                                    key={report.id}
                                    variants={item}
                                    className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
                                >
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="p-3 bg-green-50 rounded-full text-green-600">
                                            <Leaf className="w-6 h-6" />
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm text-gray-500">
                                                {new Date(report.date).toLocaleDateString()}
                                            </div>
                                            {report.location && (
                                                <div className="text-xs text-gray-400 mt-1">
                                                    {report.location}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* NPK Values */}
                                    <div className="space-y-3 mb-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <TestTube className="w-4 h-4 text-gray-400" />
                                                <span className="text-sm text-gray-600">Nitrogen (N)</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-gray-900">{report.nitrogen} kg/ha</span>
                                                <span className={`text-xs ${nStatus.color}`}>({nStatus.label})</span>
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <TestTube className="w-4 h-4 text-gray-400" />
                                                <span className="text-sm text-gray-600">Phosphorus (P)</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-gray-900">{report.phosphorus} kg/ha</span>
                                                <span className={`text-xs ${pStatus.color}`}>({pStatus.label})</span>
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <TestTube className="w-4 h-4 text-gray-400" />
                                                <span className="text-sm text-gray-600">Potassium (K)</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-gray-900">{report.potassium} kg/ha</span>
                                                <span className={`text-xs ${kStatus.color}`}>({kStatus.label})</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="border-t border-gray-100 pt-4 space-y-3">
                                        {/* pH Level */}
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Activity className="w-4 h-4 text-gray-400" />
                                                <span className="text-sm text-gray-600">pH Level</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-gray-900">{report.ph}</span>
                                                <span className={`text-xs px-2 py-1 rounded-full ${phStatus.color}`}>
                                                    {phStatus.label}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Moisture */}
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Droplets className="w-4 h-4 text-gray-400" />
                                                <span className="text-sm text-gray-600">Moisture</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-gray-900">{report.moisture}%</span>
                                                <span className={`text-xs px-2 py-1 rounded-full ${moistureStatus.color}`}>
                                                    {moistureStatus.label}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </motion.div>
                )}

                {/* Add Report Modal */}
                <Modal
                    isOpen={showAddModal}
                    onClose={() => setShowAddModal(false)}
                    title="Add Soil Report"
                >
                    <form onSubmit={handleAddReport} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label htmlFor="nitrogen" className="block text-sm font-medium text-gray-700 mb-2">
                                    Nitrogen (kg/ha) *
                                </label>
                                <input
                                    id="nitrogen"
                                    type="number"
                                    step="0.1"
                                    value={newReport.nitrogen}
                                    onChange={(e) => setNewReport({ ...newReport, nitrogen: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                                    required
                                    min="0"
                                    placeholder="e.g., 25.5"
                                />
                            </div>

                            <div>
                                <label htmlFor="phosphorus" className="block text-sm font-medium text-gray-700 mb-2">
                                    Phosphorus (kg/ha) *
                                </label>
                                <input
                                    id="phosphorus"
                                    type="number"
                                    step="0.1"
                                    value={newReport.phosphorus}
                                    onChange={(e) => setNewReport({ ...newReport, phosphorus: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                                    required
                                    min="0"
                                    placeholder="e.g., 30.0"
                                />
                            </div>

                            <div>
                                <label htmlFor="potassium" className="block text-sm font-medium text-gray-700 mb-2">
                                    Potassium (kg/ha) *
                                </label>
                                <input
                                    id="potassium"
                                    type="number"
                                    step="0.1"
                                    value={newReport.potassium}
                                    onChange={(e) => setNewReport({ ...newReport, potassium: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                                    required
                                    min="0"
                                    placeholder="e.g., 40.2"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="ph" className="block text-sm font-medium text-gray-700 mb-2">
                                    pH Level *
                                </label>
                                <input
                                    id="ph"
                                    type="number"
                                    step="0.1"
                                    value={newReport.ph}
                                    onChange={(e) => setNewReport({ ...newReport, ph: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                                    required
                                    min="0"
                                    max="14"
                                    placeholder="e.g., 6.5"
                                />
                            </div>

                            <div>
                                <label htmlFor="moisture" className="block text-sm font-medium text-gray-700 mb-2">
                                    Moisture (%) *
                                </label>
                                <input
                                    id="moisture"
                                    type="number"
                                    step="0.1"
                                    value={newReport.moisture}
                                    onChange={(e) => setNewReport({ ...newReport, moisture: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                                    required
                                    min="0"
                                    max="100"
                                    placeholder="e.g., 45.0"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                                Location (optional)
                            </label>
                            <input
                                id="location"
                                type="text"
                                value={newReport.location}
                                onChange={(e) => setNewReport({ ...newReport, location: e.target.value })}
                                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                                placeholder="e.g., North Field"
                            />
                        </div>

                        <div className="flex justify-end gap-3 pt-4">
                            <button
                                type="button"
                                onClick={() => setShowAddModal(false)}
                                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={addReportMutation.isPending}
                                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {addReportMutation.isPending ? 'Adding...' : 'Add Report'}
                            </button>
                        </div>
                    </form>
                </Modal>
            </div>
        </PageTransition>
    );
};

export default Soil;
