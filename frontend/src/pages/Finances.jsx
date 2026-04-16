import { useCallback, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Calendar, IndianRupee, LineChart, Plus, Trash2, TrendingDown, TrendingUp } from 'lucide-react';
import { Bar, BarChart as RechartsBar, CartesianGrid, Legend, Line, LineChart as RechartsLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import Input from '../components/Input';
import Modal from '../components/Modal';
import PageTransition from '../components/PageTransition';
import Select from '../components/Select';
import { SkeletonCard, SkeletonTable } from '../components/SkeletonLoader';
import { useAddExpense, useCrops, useDeleteExpense, useExpenses, useExpensesSummary } from '../hooks/useApi';

const Finances = () => {
    const [showAddModal, setShowAddModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [expenseToDelete, setExpenseToDelete] = useState(null);
    const [newTransaction, setNewTransaction] = useState({
        title: '',
        amount: '',
        type: 'expense',
        date: new Date().toISOString().split('T')[0],
        crop_id: ''
    });

    // Use React Query hooks
    const { data: expenses = [], isLoading: expensesLoading } = useExpenses();
    const { data: summary = { total_income: 0, total_expense: 0, profit: 0 }, isLoading: summaryLoading } = useExpensesSummary();
    const { data: crops = [] } = useCrops();
    const addExpenseMutation = useAddExpense();
    const deleteExpenseMutation = useDeleteExpense();


    const handleAddTransaction = useCallback(async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...newTransaction,
                amount: parseFloat(newTransaction.amount),
                crop_id: newTransaction.crop_id ? parseInt(newTransaction.crop_id) : null
            };
            await addExpenseMutation.mutateAsync(payload);
            setShowAddModal(false);
            setNewTransaction({
                title: '',
                amount: '',
                type: 'expense',
                date: new Date().toISOString().split('T')[0],
                crop_id: ''
            });
        } catch (error) {
            // Error already handled by mutation
        }
    }, [addExpenseMutation, newTransaction]);

    const handleDeleteClick = useCallback((expense) => {
        setExpenseToDelete(expense);
        setShowDeleteModal(true);
    }, []);

    const handleDeleteConfirm = useCallback(async () => {
        if (!expenseToDelete) return;
        
        try {
            await deleteExpenseMutation.mutateAsync(expenseToDelete.id);
            setShowDeleteModal(false);
            setExpenseToDelete(null);
        } catch (error) {
            // Error already handled by mutation
        }
    }, [deleteExpenseMutation, expenseToDelete]);

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

    // Process data for charts
    const chartData = useMemo(() => {
        if (!expenses || expenses.length === 0) return { timelineData: [], categoryData: [] };

        // Timeline data (income vs expenses by date)
        const dateMap = {};
        expenses.forEach(exp => {
            const date = exp.date || 'Unknown';
            if (!dateMap[date]) {
                dateMap[date] = { date, income: 0, expense: 0 };
            }
            if (exp.type === 'income') {
                dateMap[date].income += exp.amount;
            } else {
                dateMap[date].expense += exp.amount;
            }
        });

        const timelineData = Object.values(dateMap)
            .sort((a, b) => new Date(a.date) - new Date(b.date))
            .slice(-10); // Last 10 dates

        // Category data (expenses by category)
        const categoryMap = {};
        expenses.forEach(exp => {
            if (exp.type === 'expense') {
                const category = exp.category || exp.title.split(' ')[0] || 'Other';
                categoryMap[category] = (categoryMap[category] || 0) + exp.amount;
            }
        });

        const categoryData = Object.entries(categoryMap)
            .map(([category, amount]) => ({ category, amount }))
            .sort((a, b) => b.amount - a.amount)
            .slice(0, 8); // Top 8 categories

        return { timelineData, categoryData };
    }, [expenses]);

    return (
        <PageTransition>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-gray-900">Financial Overview</h1>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        aria-label="Add transaction"
                    >
                        <Plus className="w-4 h-4" />
                        Add Transaction
                    </button>
                </div>

                {/* Summary Cards */}
                {summaryLoading ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                    </div>
                ) : (
                    <motion.div
                        variants={container}
                        initial="hidden"
                        animate="show"
                        className="grid grid-cols-1 md:grid-cols-3 gap-6"
                    >
                    <motion.div variants={item} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-green-50 rounded-full text-green-600">
                                <TrendingUp className="w-6 h-6" />
                            </div>
                            <div>
                                <div className="text-sm text-gray-500">Total Income</div>
                                <div className="text-2xl font-bold text-gray-900">₹{summary.total_income.toLocaleString()}</div>
                            </div>
                        </div>
                    </motion.div>

                    <motion.div variants={item} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-red-50 rounded-full text-red-600">
                                <TrendingDown className="w-6 h-6" />
                            </div>
                            <div>
                                <div className="text-sm text-gray-500">Total Expenses</div>
                                <div className="text-2xl font-bold text-gray-900">₹{summary.total_expense.toLocaleString()}</div>
                            </div>
                        </div>
                    </motion.div>

                    <motion.div variants={item} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-blue-50 rounded-full text-blue-600">
                                <IndianRupee className="w-6 h-6" />
                            </div>
                            <div>
                                <div className="text-sm text-gray-500">Net Profit</div>
                                <div className={`text-2xl font-bold ${summary.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    ₹{summary.profit.toLocaleString()}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </motion.div>
                )}

                {/* Transactions List */}
                {expensesLoading ? (
                    <SkeletonTable rows={5} />
                ) : expenses.length === 0 ? (
                    <EmptyState
                        icon={IndianRupee}
                        title="No transactions yet"
                        description="Start tracking your farm's income and expenses."
                        action={() => setShowAddModal(true)}
                        actionLabel="Add Your First Transaction"
                    />
                ) : (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
                    >
                        <div className="p-6 border-b border-gray-100">
                            <h2 className="text-lg font-semibold text-gray-900">Recent Transactions</h2>
                        </div>
                        <div className="divide-y divide-gray-100">
                            {expenses.map((expense) => (
                                <div key={expense.id} className="p-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-2 rounded-lg ${expense.type === 'income' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
                                            }`}>
                                            {expense.type === 'income' ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                                        </div>
                                        <div>
                                            <div className="font-medium text-gray-900">{expense.title}</div>
                                            <div className="text-sm text-gray-500 flex items-center gap-2">
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {expense.date}
                                                </span>
                                                {expense.crop_name && (
                                                    <span className="px-2 py-0.5 bg-green-50 text-green-700 rounded text-xs font-medium">
                                                        {expense.crop_name}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className={`font-semibold ${expense.type === 'income' ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            {expense.type === 'income' ? '+' : '-'}₹{expense.amount.toLocaleString()}
                                        </div>
                                        <button
                                            onClick={() => handleDeleteClick(expense)}
                                            className="text-gray-400 hover:text-red-500 transition-colors p-2"
                                            aria-label="Delete transaction"
                                        >
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* Analytics Charts */}
                {!expensesLoading && expenses.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="space-y-6"
                    >
                        {/* Income vs Expenses Timeline */}
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <div className="flex items-center gap-2 mb-6">
                                <LineChart className="w-5 h-5 text-blue-600" />
                                <h2 className="text-lg font-semibold text-gray-900">Income vs Expenses Over Time</h2>
                            </div>
                            {chartData.timelineData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <RechartsLine data={chartData.timelineData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                        <XAxis 
                                            dataKey="date" 
                                            stroke="#6b7280"
                                            style={{ fontSize: '12px' }}
                                            tickFormatter={(value) => {
                                                const date = new Date(value);
                                                return `${date.getMonth() + 1}/${date.getDate()}`;
                                            }}
                                        />
                                        <YAxis 
                                            stroke="#6b7280"
                                            style={{ fontSize: '12px' }}
                                            tickFormatter={(value) => `₹${value.toLocaleString()}`}
                                        />
                                        <Tooltip 
                                            contentStyle={{
                                                backgroundColor: '#fff',
                                                border: '1px solid #e5e7eb',
                                                borderRadius: '8px',
                                                padding: '8px 12px'
                                            }}
                                            formatter={(value) => [`₹${value.toLocaleString()}`, '']}
                                            labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
                                        />
                                        <Legend 
                                            wrapperStyle={{ paddingTop: '20px' }}
                                            iconType="circle"
                                        />
                                        <Line 
                                            type="monotone" 
                                            dataKey="income" 
                                            stroke="#10b981" 
                                            strokeWidth={2}
                                            dot={{ fill: '#10b981', r: 4 }}
                                            activeDot={{ r: 6 }}
                                            name="Income"
                                        />
                                        <Line 
                                            type="monotone" 
                                            dataKey="expense" 
                                            stroke="#ef4444" 
                                            strokeWidth={2}
                                            dot={{ fill: '#ef4444', r: 4 }}
                                            activeDot={{ r: 6 }}
                                            name="Expense"
                                        />
                                    </RechartsLine>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-64 flex items-center justify-center text-gray-500">
                                    Not enough data to display timeline
                                </div>
                            )}
                        </div>

                        {/* Category-wise Expenses */}
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <div className="flex items-center gap-2 mb-6">
                                <BarChart3 className="w-5 h-5 text-purple-600" />
                                <h2 className="text-lg font-semibold text-gray-900">Expenses by Category</h2>
                            </div>
                            {chartData.categoryData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <RechartsBar data={chartData.categoryData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                        <XAxis 
                                            dataKey="category" 
                                            stroke="#6b7280"
                                            style={{ fontSize: '12px' }}
                                            angle={-45}
                                            textAnchor="end"
                                            height={80}
                                        />
                                        <YAxis 
                                            stroke="#6b7280"
                                            style={{ fontSize: '12px' }}
                                            tickFormatter={(value) => `₹${value.toLocaleString()}`}
                                        />
                                        <Tooltip 
                                            contentStyle={{
                                                backgroundColor: '#fff',
                                                border: '1px solid #e5e7eb',
                                                borderRadius: '8px',
                                                padding: '8px 12px'
                                            }}
                                            formatter={(value) => [`₹${value.toLocaleString()}`, 'Amount']}
                                            labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
                                            cursor={{ fill: 'rgba(139, 92, 246, 0.1)' }}
                                        />
                                        <Bar 
                                            dataKey="amount" 
                                            fill="#8b5cf6" 
                                            radius={[8, 8, 0, 0]}
                                            name="Amount"
                                        />
                                    </RechartsBar>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-64 flex items-center justify-center text-gray-500">
                                    No expense categories to display
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* Add Transaction Modal */}
                <Modal
                    isOpen={showAddModal}
                    onClose={() => setShowAddModal(false)}
                    title="Add Transaction"
                >
                    <form onSubmit={handleAddTransaction} className="space-y-4">
                        <Input
                            label="Title"
                            id="title"
                            type="text"
                            required
                            value={newTransaction.title}
                            onChange={(e) => setNewTransaction({ ...newTransaction, title: e.target.value })}
                            placeholder="e.g., Seeds, Harvest Sale"
                        />
                        <div className="grid grid-cols-2 gap-4">
                            <Input
                                label="Amount (₹)"
                                id="amount"
                                type="number"
                                required
                                min="0"
                                step="0.01"
                                value={newTransaction.amount}
                                onChange={(e) => setNewTransaction({ ...newTransaction, amount: e.target.value })}
                            />
                            <Select
                                label="Type"
                                id="type"
                                value={newTransaction.type}
                                onChange={(e) => setNewTransaction({ ...newTransaction, type: e.target.value })}
                                options={[
                                    { value: 'expense', label: 'Expense' },
                                    { value: 'income', label: 'Income' }
                                ]}
                            />
                        </div>
                        <Input
                            label="Date"
                            id="date"
                            type="date"
                            required
                            value={newTransaction.date}
                            onChange={(e) => setNewTransaction({ ...newTransaction, date: e.target.value })}
                        />
                        <Select
                            label="Link to Crop (Optional)"
                            id="crop"
                            value={newTransaction.crop_id}
                            onChange={(e) => setNewTransaction({ ...newTransaction, crop_id: e.target.value })}
                            options={[
                                { value: '', label: 'None' },
                                ...crops.map((crop) => ({
                                    value: crop.id,
                                    label: `${crop.crop} - ${crop.plot}`
                                }))
                            ]}
                        />
                        <div className="flex gap-3 pt-2">
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={() => setShowAddModal(false)}
                                disabled={addExpenseMutation.isPending}
                                fullWidth
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                variant="primary"
                                disabled={addExpenseMutation.isPending}
                                fullWidth
                            >
                                {addExpenseMutation.isPending ? 'Adding...' : 'Add Transaction'}
                            </Button>
                        </div>
                    </form>
                </Modal>

                {/* Delete Confirmation Modal */}
                <Modal
                    isOpen={showDeleteModal}
                    onClose={() => {
                        setShowDeleteModal(false);
                        setExpenseToDelete(null);
                    }}
                    title="Delete Transaction"
                >
                    <div className="space-y-4">
                        <p className="text-gray-600">
                            Are you sure you want to delete this transaction? This action cannot be undone.
                        </p>
                        {expenseToDelete && (
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="font-medium text-gray-900">{expenseToDelete.title}</div>
                                <div className={`text-sm font-semibold mt-1 ${expenseToDelete.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                                    {expenseToDelete.type === 'income' ? '+' : '-'}₹{expenseToDelete.amount.toLocaleString()}
                                </div>
                            </div>
                        )}
                        <div className="flex gap-3 pt-2">
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={() => {
                                    setShowDeleteModal(false);
                                    setExpenseToDelete(null);
                                }}
                                disabled={deleteExpenseMutation.isPending}
                                fullWidth
                            >
                                Cancel
                            </Button>
                            <Button
                                type="button"
                                variant="danger"
                                onClick={handleDeleteConfirm}
                                disabled={deleteExpenseMutation.isPending}
                                fullWidth
                            >
                                {deleteExpenseMutation.isPending ? 'Deleting...' : 'Delete'}
                            </Button>
                        </div>
                    </div>
                </Modal>
            </div>
        </PageTransition>
    );
};

export default Finances;
