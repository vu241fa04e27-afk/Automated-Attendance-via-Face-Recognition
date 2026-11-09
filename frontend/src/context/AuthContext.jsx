import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('attendance_token'));
  const [admin, setAdmin] = useState(() => {
    const saved = localStorage.getItem('attendance_admin');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      if (token.startsWith('demo_token_')) {
        setLoading(false);
        return;
      }
      api.get('/api/auth/me')
        .then(res => {
          setAdmin(res.data.admin);
          localStorage.setItem('attendance_admin', JSON.stringify(res.data.admin));
        })
        .catch(() => {
          if (!token.startsWith('demo_token_')) {
            logout();
          }
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (username, password) => {
    try {
      const res = await api.post('/api/auth/login', { username, password });
      const { access_token, admin: adminData } = res.data;
      localStorage.setItem('attendance_token', access_token);
      localStorage.setItem('attendance_admin', JSON.stringify(adminData));
      setToken(access_token);
      setAdmin(adminData);
      return adminData;
    } catch (err) {
      // If backend is not reached (e.g. running on Vercel without backend env var) or 404
      if (
        (err.response?.status === 404 || !err.response || err.code === 'ERR_NETWORK') &&
        username === 'admin' &&
        password === 'admin123'
      ) {
        const demoAdmin = {
          admin_id: 1,
          username: 'admin',
          full_name: 'System Administrator',
          created_at: new Date().toISOString(),
        };
        const demoToken = 'demo_token_' + Date.now();
        localStorage.setItem('attendance_token', demoToken);
        localStorage.setItem('attendance_admin', JSON.stringify(demoAdmin));
        setToken(demoToken);
        setAdmin(demoAdmin);
        return demoAdmin;
      }
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('attendance_token');
    localStorage.removeItem('attendance_admin');
    setToken(null);
    setAdmin(null);
  };

  return (
    <AuthContext.Provider value={{ token, admin, isAuthenticated: !!token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

