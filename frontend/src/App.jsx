import { lazy, Suspense } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { queryClient } from './lib/queryClient';

// Lazy load pages for code splitting
const Chat = lazy(() => import('./pages/Chat'));
const Crops = lazy(() => import('./pages/Crops'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Finances = lazy(() => import('./pages/Finances'));
const Login = lazy(() => import('./pages/Login'));
const Prices = lazy(() => import('./pages/Prices'));
const Register = lazy(() => import('./pages/Register'));
const Soil = lazy(() => import('./pages/Soil'));
const Weather = lazy(() => import('./pages/Weather'));

// Loading component
const LoadingFallback = () => (
    <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
    </div>
);

function App() {
    return (
        <ErrorBoundary>
            <QueryClientProvider client={queryClient}>
                <AuthProvider>
                    <Router>
                        <Suspense fallback={<LoadingFallback />}>
                            <Routes>
                        {/* Public Routes */}
                        <Route path="/login" element={<Login />} />
                        <Route path="/register" element={<Register />} />

                    {/* Protected Routes */}
                    <Route path="/" element={
                        <ProtectedRoute>
                            <Layout>
                                <Dashboard />
                            </Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/weather" element={
                        <ProtectedRoute>
                            <Layout>
                                <Weather />
                            </Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/crops" element={
                        <ProtectedRoute>
                            <Layout>
                                <Crops />
                            </Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/finances" element={
                        <ProtectedRoute>
                            <Layout>
                                <Finances />
                            </Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/prices" element={
                        <ProtectedRoute>
                            <Layout>
                                <Prices />
                            </Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/soil" element={
                        <ProtectedRoute>
                            <Layout>
                                <Soil />
                            </Layout>
                        </ProtectedRoute>
                    } />
                    <Route path="/chat" element={
                        <ProtectedRoute>
                            <Layout>
                                <Chat />
                            </Layout>
                        </ProtectedRoute>
                    } />
                        </Routes>
                    </Suspense>
                </Router>
            </AuthProvider>
        </QueryClientProvider>
        </ErrorBoundary>
    );
}

export default App;
