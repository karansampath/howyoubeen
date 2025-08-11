'use client';

import { Header } from './Header';
import { useAuth } from '@/components/auth/AuthContext';

export function AuthenticatedHeader() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
      // Redirect anyway since logout clears local state
      window.location.href = '/login';
    }
  };

  return (
    <Header 
      user={user ? {
        username: user.username,
        full_name: user.full_name
      } : undefined}
      onLogout={handleLogout}
    />
  );
}
