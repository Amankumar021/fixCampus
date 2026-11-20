import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    try { return savedUser ? JSON.parse(savedUser) : null; } catch { return null; }
  });
  const [loading, setLoading] = useState(true);
  const clearSession = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);
  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    const accessToken = localStorage.getItem('access_token');
    if (refreshToken && accessToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Clear the local session even if the server is offline.
      }
    }
    clearSession();
  }, [clearSession]);
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      apiClient.get('/auth/me')
        .then((res) => {
          setUser(res.data);
          localStorage.setItem('user', JSON.stringify(res.data));
        })
        .catch(() => {
          clearSession();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [clearSession]);

  const login = async (email, password) => {
    const res = await apiClient.post('/auth/login', { email, password });
    const { access_token, refresh_token } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    const userProfile = await apiClient.get('/auth/me');
    setUser(userProfile.data);
    localStorage.setItem('user', JSON.stringify(userProfile.data));
    return userProfile.data;
  };

  const register = async (email, password, full_name, phone_number) => {
    return apiClient.post('/auth/register', {
      email,
      password,
      full_name,
      phone_number,
    });
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
