export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'employee';
  companyId: number;
  companyName: string;
  companyLogo?: string;
  employeeId?: number;
}

const MOCK_ADMIN: User = {
  id: 1,
  name: 'Admin HR',
  email: 'admin@company.com',
  role: 'admin',
  companyId: 1,
  companyName: 'PT Maju Bersama',
  companyLogo: undefined,
};

function setAuthCookie(): void {
  document.cookie = 'auth_token=authenticated; path=/; max-age=86400; SameSite=Lax';
}

function clearAuthCookie(): void {
  document.cookie = 'auth_token=; path=/; max-age=0';
}

export function login(email: string, password: string): { success: boolean; user?: User; error?: string } {
  // Admin login
  if (email === 'admin@company.com' && password === 'password123') {
    localStorage.setItem('user', JSON.stringify(MOCK_ADMIN));
    setAuthCookie();
    return { success: true, user: MOCK_ADMIN };
  }
  // Employee login (demo): employee email pattern employee{id}@company.com
  const employeeMatch = email.match(/^employee(\d+)@company\.com$/);
  if (employeeMatch && password.length >= 6) {
    const employeeId = Number(employeeMatch[1]);
    const user: User = {
      id: 1000 + employeeId,
      name: `Karyawan ${employeeId}`,
      email,
      role: 'employee',
      companyId: 1,
      companyName: 'PT Maju Bersama',
      employeeId,
    };
    localStorage.setItem('user', JSON.stringify(user));
    setAuthCookie();
    return { success: true, user };
  }
  return { success: false, error: 'Email atau password salah' };
}

export function logout(): void {
  localStorage.removeItem('user');
  clearAuthCookie();
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  const stored = localStorage.getItem('user');
  if (!stored) return null;
  try {
    return JSON.parse(stored) as User;
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return getUser() !== null;
}
