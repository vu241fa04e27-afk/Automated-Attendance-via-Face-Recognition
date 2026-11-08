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
      api.get('/api/auth/me')
        .then(res => {
          setAdmin(res.data.admin);
          localStorage.setItem('attendance_admin', JSON.stringify(res.data.admin));
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (username, password) => {
    const res = await api.post('/api/auth/login', { username, password });
    const { access_token, admin: adminData } = res.data;
    localStorage.setItem('attendance_token', access_token);
    localStorage.setItem('attendance_admin', JSON.stringify(adminData));
    setToken(access_token);
    setAdmin(adminData);
    return adminData;
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

