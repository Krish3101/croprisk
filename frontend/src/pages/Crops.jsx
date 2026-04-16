import { useCallback, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Map, Plus, Sprout, Trash2 } from 'lucide-react';

import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import Input from '../components/Input';
import Modal from '../components/Modal';
import PageTransition from '../components/PageTransition';
import { SkeletonList } from '../components/SkeletonLoader';
import { CROP_STAGES } from '../constants';
import { useAddCrop, useCrops, useDeleteCrop, useUpdateCropStage } from '../hooks/useApi';

const Crops = () => {
    const [showAddModal, setShowAddModal] = useState(false);
    const [newCrop, setNewCrop] = useState({ crop: '', plot: '' });

    // Use React Query hooks
    const { data: crops = [], isLoading: loading } = useCrops();
    const addCropMutation = useAddCrop();
    const deleteCropMutation = useDeleteCrop();
    const updateStageMutation = useUpdateCropStage();

    const handleAddCrop = useCallback(async (e) => {
        e.preventDefault();
        try {
            await addCropMutation.mutateAsync(newCrop);
            setShowAddModal(false);
            setNewCrop({ crop: '', plot: '' });
        } catch (error) {
            console.error('Failed to add crop:', error);
        }
    }, [addCropMutation, newCrop]);

    const handleDeleteCrop = useCallback(async (id) => {
        if (window.confirm('Are you sure you want to delete this crop?')) {
            try {
                await deleteCropMutation.mutateAsync(id);
            } catch (error) {
                // Error already handled by mutation
            }
        }
    }, [deleteCropMutation]);

    const handleStageUpdate = useCallback(async (id, stage) => {
        try {
            await updateStageMutation.mutateAsync({ cropId: id, stage });
        } catch (error) {
            // Error already handled by mutation
        }
    }, [updateStageMutation]);

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
                    <h1 className="text-2xl font-bold text-gray-900">Crop Management</h1>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        aria-label="Add new crop"
                    >
                        <Plus className="w-4 h-4" />
                        Add Crop
                    </button>
                </div>

                {loading ? (
                    <SkeletonList count={6} />
                ) : crops.length === 0 ? (
                    <EmptyState
                        icon={Sprout}
                        title="No crops found"
                        description="Start by adding your first crop to track."
                        action={() => setShowAddModal(true)}
                        actionLabel="Add Your First Crop"
                    />
                ) : (
                    <motion.div
                        variants={container}
                        initial="hidden"
                        animate="show"
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                    >
                        {crops.map((crop) => (
                            <motion.div
                                key={crop.id}
                                variants={item}
                                className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-3 bg-green-50 rounded-full text-green-600">
                                        <Sprout className="w-6 h-6" />
                                    </div>
                                    <button
                                        onClick={() => handleDeleteCrop(crop.id)}
                                        className="text-gray-400 hover:text-red-500 transition-colors"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>

                                <h3 className="text-lg font-semibold text-gray-900 mb-1">{crop.crop}</h3>
                                <div className="space-y-2 text-sm text-gray-600">
                                    <div className="flex items-center gap-2">
                                        <Map className="w-4 h-4" />
                                        <span>{crop.plot}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4" />
                                        <span>Sown: {crop.sown_date}</span>
                                    </div>
                                </div>

                                <div className="mt-4 pt-4 border-t border-gray-100">
                                    <label htmlFor={`stage-${crop.id}`} className="block text-sm font-medium text-gray-500 mb-2">
                                        Growth Stage
                                    </label>
                                    <select
                                        id={`stage-${crop.id}`}
                                        value={crop.stage}
                                        onChange={(e) => handleStageUpdate(crop.id, e.target.value)}
                                        className="w-full px-3 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium border border-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 hover:bg-blue-100 transition-colors cursor-pointer"
                                        disabled={updateStageMutation.isPending}
                                    >
                                        {CROP_STAGES.map((stage) => (
                                            <option key={stage} value={stage}>
                                                {stage}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </motion.div>
                        ))}
                    </motion.div>
                )}

                {/* Add Crop Modal */}
                <Modal
                    isOpen={showAddModal}
                    onClose={() => setShowAddModal(false)}
                    title="Add New Crop"
                >
                    <form onSubmit={handleAddCrop} className="space-y-4">
                        <Input
                            label="Crop Name"
                            id="crop-name"
                            type="text"
                            required
                            value={newCrop.crop}
                            onChange={(e) => setNewCrop({ ...newCrop, crop: e.target.value })}
                            placeholder="e.g., Wheat, Rice"
                        />
                        <Input
                            label="Plot/Field Name"
                            id="plot-name"
                            type="text"
                            required
                            value={newCrop.plot}
                            onChange={(e) => setNewCrop({ ...newCrop, plot: e.target.value })}
                            placeholder="e.g., North Field"
                        />
                        <div className="flex gap-3 pt-2">
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={() => setShowAddModal(false)}
                                disabled={addCropMutation.isPending}
                                fullWidth
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                variant="primary"
                                disabled={addCropMutation.isPending}
                                fullWidth
                            >
                                {addCropMutation.isPending ? 'Adding...' : 'Add Crop'}
                            </Button>
                        </div>
                    </form>
                </Modal>
            </div>
        </PageTransition>
    );
};

export default Crops;
