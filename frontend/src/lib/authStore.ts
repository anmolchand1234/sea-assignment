import { create } from 'zustand';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'passenger' | 'dispatcher' | 'admin' | 'driver';
}

interface AuthState {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  initFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  setAuth: (user, token) => {
    localStorage.setItem('wayline_token', token);
    localStorage.setItem('wayline_user', JSON.stringify(user));
    set({ user, token });
  },
  logout: () => {
    localStorage.removeItem('wayline_token');
    localStorage.removeItem('wayline_user');
    set({ user: null, token: null });
  },
  initFromStorage: () => {
    const token = localStorage.getItem('wayline_token');
    const storedUser = localStorage.getItem('wayline_user');
    if (token && storedUser) {
      try {
        set({ token, user: JSON.parse(storedUser) });
      } catch {
        set({ token: null, user: null });
      }
    }
  },
}));
