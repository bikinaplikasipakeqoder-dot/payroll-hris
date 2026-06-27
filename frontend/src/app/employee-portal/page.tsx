'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  User,
  Banknote,
  Gift,
  Clock,
  FileText,
  LogOut,
  Loader2,
  AlertCircle,
  RefreshCw,
  Briefcase,
  Building2,
  Award,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { formatIDR } from '@/lib/utils';
import { getUser, logout } from '@/lib/auth';
import EmployeeAttendance from '@/components/employee-portal/EmployeeAttendance';

// ─── Types ───────────────────────────────────────────────────────────────────

interface EmployeeProfile {
  id: number;
  employee_code: string;
  first_name: string;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  religion: string | null;
  join_date: string;
  base_salary: string;
  ptkp_status: string;
  department_id: number | null;
  position_id: number | null;
  grade_id: number | null;
  is_active: boolean;
}

interface EmployeeAllowance {
  id: number;
  allowance_type_name: string;
  amount: string;
  effective_date: string;
  end_date: string | null;
  is_active: boolean;
}

interface Payslip {
  id: number;
  payroll_run_id: number;
  payslip_number: string;
  basic_salary: number;
  total_allowances: number;
  bonus_amount: number;
  gross_salary: number;
  total_deductions: number;
  net_salary: number;
  created_at: string;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function EmployeePortalPage() {
  const router = useRouter();
  const user = getUser();
  const employeeId = user?.employeeId || 1;

  const [activeTab, setActiveTab] = useState<'profile' | 'compensation' | 'payslips' | 'attendance'>('profile');
  const [profile, setProfile] = useState<EmployeeProfile | null>(null);
  const [allowances, setAllowances] = useState<EmployeeAllowance[]>([]);
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profileData, allowancesData, payslipsData] = await Promise.all([
        api.get<EmployeeProfile>(`/api/v1/employees/${employeeId}/profile`),
        api.get<EmployeeAllowance[]>(`/api/v1/employees/${employeeId}/allowances`),
        api.get<Payslip[]>(`/api/v1/employees/${employeeId}/payslips?limit=50`),
      ]);
      setProfile(profileData);
      setAllowances(allowancesData);
      setPayslips(payslipsData);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Tidak dapat memuat data.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role !== 'employee') {
      // Allow admin to view demo portal for employee 1
    }
    fetchData();
  }, [employeeId]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const fullName = profile ? `${profile.first_name} ${profile.last_name || ''}`.trim() : user?.name || 'Karyawan';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
        <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
        <p className="text-gray-700 mb-4">{error || 'Data karyawan tidak ditemukan.'}</p>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-emerald-600 border border-emerald-300 rounded-lg hover:bg-emerald-50 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Coba Lagi
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center">
              <span className="text-white font-bold">PP</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">Portal Karyawan</h1>
              <p className="text-xs text-gray-500">{user?.companyName}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-gray-900">{fullName}</p>
              <p className="text-xs text-gray-500">{profile.employee_code}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-red-600 transition-colors"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex space-x-1 overflow-x-auto">
            {[
              { id: 'profile', label: 'Profil', icon: User },
              { id: 'compensation', label: 'Gaji & Tunjangan', icon: Banknote },
              { id: 'payslips', label: 'Slip Gaji', icon: FileText },
              { id: 'attendance', label: 'Kehadiran', icon: Clock },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'border-emerald-500 text-emerald-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        {activeTab === 'profile' && <ProfileTab profile={profile} />}
        {activeTab === 'compensation' && <CompensationTab profile={profile} allowances={allowances} />}
        {activeTab === 'payslips' && <PayslipsTab payslips={payslips} />}
        {activeTab === 'attendance' && <EmployeeAttendance employeeId={employeeId} />}
      </main>
    </div>
  );
}

// ─── Profile Tab ─────────────────────────────────────────────────────────────

function ProfileTab({ profile }: { profile: EmployeeProfile }) {
  const fields = [
    { label: 'Nama Lengkap', value: `${profile.first_name} ${profile.last_name || ''}`.trim(), icon: User },
    { label: 'NIK / Kode Karyawan', value: profile.employee_code, icon: Briefcase },
    { label: 'Email', value: profile.email || '-', icon: Building2 },
    { label: 'Telepon', value: profile.phone || '-', icon: Building2 },
    { label: 'Agama', value: profile.religion || '-', icon: Award },
    { label: 'Status PTKP', value: profile.ptkp_status, icon: FileText },
    { label: 'Tanggal Bergabung', value: profile.join_date, icon: Clock },
    { label: 'Status', value: profile.is_active ? 'Aktif' : 'Nonaktif', icon: User },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Profil Karyawan</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {fields.map((field) => (
          <div key={field.label} className="p-4 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-1">{field.label}</p>
            <p className="text-sm font-medium text-gray-900">{field.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Compensation Tab ────────────────────────────────────────────────────────

function CompensationTab({
  profile,
  allowances,
}: {
  profile: EmployeeProfile;
  allowances: EmployeeAllowance[];
}) {
  const activeAllowances = allowances.filter((a) => a.is_active);
  const totalAllowances = activeAllowances.reduce((sum, a) => sum + Number(a.amount), 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryCard label="Gaji Pokok" value={formatIDR(Number(profile.base_salary))} icon={Banknote} />
        <SummaryCard label="Total Tunjangan Aktif" value={formatIDR(totalAllowances)} icon={Gift} />
        <SummaryCard
          label="Gaji + Tunjangan"
          value={formatIDR(Number(profile.base_salary) + totalAllowances)}
          icon={Banknote}
          highlight
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">Rincian Tunjangan</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-500">Jenis Tunjangan</th>
                <th className="text-right py-3 px-4 font-medium text-gray-500">Jumlah</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500">Efektif</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {activeAllowances.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-8 text-gray-500">
                    Tidak ada tunjangan aktif.
                  </td>
                </tr>
              ) : (
                activeAllowances.map((allowance) => (
                  <tr key={allowance.id}>
                    <td className="py-3 px-4 text-gray-900">{allowance.allowance_type_name}</td>
                    <td className="py-3 px-4 text-right font-mono">{formatIDR(Number(allowance.amount))}</td>
                    <td className="py-3 px-4 text-gray-600">
                      {allowance.effective_date} s/d {allowance.end_date || 'sekarang'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-700">
                        Aktif
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Payslips Tab ────────────────────────────────────────────────────────────

function PayslipsTab({ payslips }: { payslips: Payslip[] }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="text-base font-semibold text-gray-900">Riwayat Slip Gaji</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-gray-500">No. Slip</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500">Gaji Pokok</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500">Tunjangan</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500">Bonus</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500">Bruto</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500">Potongan</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500">Take Home Pay</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {payslips.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-gray-500">
                  Belum ada riwayat slip gaji.
                </td>
              </tr>
            ) : (
              payslips.map((payslip) => (
                <tr key={payslip.id}>
                  <td className="py-3 px-4 text-gray-900">{payslip.payslip_number}</td>
                  <td className="py-3 px-4 text-right font-mono">{formatIDR(payslip.basic_salary)}</td>
                  <td className="py-3 px-4 text-right font-mono">{formatIDR(payslip.total_allowances)}</td>
                  <td className="py-3 px-4 text-right font-mono">{formatIDR(payslip.bonus_amount)}</td>
                  <td className="py-3 px-4 text-right font-mono">{formatIDR(payslip.gross_salary)}</td>
                  <td className="py-3 px-4 text-right font-mono">{formatIDR(payslip.total_deductions)}</td>
                  <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-700">
                    {formatIDR(payslip.net_salary)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Summary Card ────────────────────────────────────────────────────────────

function SummaryCard({
  label,
  value,
  icon: Icon,
  highlight = false,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl p-4 border ${highlight ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-gray-200'}`}>
      <div className="flex items-center gap-3 mb-2">
        <Icon className={`w-5 h-5 ${highlight ? 'text-emerald-600' : 'text-gray-400'}`} />
        <p className="text-sm text-gray-500">{label}</p>
      </div>
      <p className={`text-xl font-bold ${highlight ? 'text-emerald-700' : 'text-gray-900'}`}>{value}</p>
    </div>
  );
}
