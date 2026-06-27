'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { LayoutDashboard, Users, Banknote, Clock, Settings, LogOut, MessageSquare, FileText, Receipt, FileOutput, Award, Gift, Wallet } from 'lucide-react';
import { getUser, logout, User } from '@/lib/auth';

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { label: 'Karyawan', icon: Users, href: '/employees' },
  { label: 'Payroll', icon: Banknote, href: '/payroll' },
  { label: 'Bonus', icon: Award, href: '/bonuses' },
  { label: 'THR', icon: Gift, href: '/thr' },
  { label: 'Reimbursement', icon: Wallet, href: '/reimbursements' },
  { label: 'Slip Gaji', icon: Receipt, href: '/payslips' },
  { label: 'Kelola Payslip', icon: FileOutput, href: '/payslip-management' },
  { label: 'Kehadiran', icon: Clock, href: '/attendance' },
  { label: 'AI Chat', icon: MessageSquare, href: '/ai-chat' },
  { label: 'AI Reports', icon: FileText, href: '/ai-reports' },
  { label: 'Pengaturan', icon: Settings, href: '/settings' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  const handleLogout = () => {
    logout();
    window.location.href = '/';
  };

  return (
    <aside className="fixed left-0 top-0 w-60 h-screen bg-sidebar flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5">
        <div className="w-9 h-9 rounded-full bg-primary-500 flex items-center justify-center">
          <span className="text-white text-sm font-bold">PP</span>
        </div>
        <span className="text-white text-lg font-semibold">PayrollPro</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 mt-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 mx-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-slate-700/50 text-white border-l-[3px] border-primary-500 pl-[13px]'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="border-t border-slate-700 px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
            <span className="text-white text-xs font-medium">
              {user?.name?.split(' ').map((n) => n[0]).join('').slice(0, 2) || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.name || 'User'}</p>
            <p className="text-xs text-slate-400 truncate">{user?.role || 'Admin'}</p>
          </div>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
