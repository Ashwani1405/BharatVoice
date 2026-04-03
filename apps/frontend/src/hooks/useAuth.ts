/**
 * Sprint 1 — Auth Hook
 */
// TODO: Sprint 1 — implement auth context logic

import { useState } from 'react';

export function useAuth() {
  const [user, setUser] = useState(null);

  const login = (token) => {
    localStorage.setItem('auth_token', token);
    setUser({ id: '123', name: 'Test User' });
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  return { user, login, logout, isAuthenticated: !!user };
}
