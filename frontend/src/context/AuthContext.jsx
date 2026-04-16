import { createContext, useState, useEffect } from 'react';
import { authApi } from '../services/api';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const userData = await authApi.getProfile();
                setUser(userData);
            } catch (error) {
                localStorage.removeItem('token');
                setUser(null);
            }
        }
        setLoading(false);
    };

    const login = async (username, password) => {
        const response = await authApi.login(username, password);
        localStorage.setItem('token', response.access_token);
        await checkAuth();
        return response;
    };

    const register = async (userData) => {
        const response = await authApi.register(userData);
        return response;
    };

    const logout = async () => {
        try {
            await authApi.logout();
        } catch (error) {
            // Silently handle logout errors
        } finally {
            localStorage.removeItem('token');
            setUser(null);
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

