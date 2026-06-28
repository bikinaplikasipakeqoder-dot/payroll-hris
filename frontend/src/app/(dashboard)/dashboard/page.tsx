"use client";

import { useState, useEffect } from "react";
import { Users, Banknote, Clock, TrendingUp } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import StatCard from "@/components/dashboard/StatCard";
import PayrollSummaryChart from "@/components/dashboard/PayrollSummaryChart";
import EmployeeChart from "@/components/dashboard/EmployeeChart";
import RecentActivity from "@/components/dashboard/RecentActivity";

interface DashboardStats {
  total_employees: number;
  employees_by_department: { department: string; count: number }[];
  active_payroll_runs: number;
  pending_overtime: number;
  total_payroll_this_month: number;
  monthly_trend: { period: string; month: string; amount: number }[];
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.get<DashboardStats>(
          "/api/v1/dashboard/stats?company_id=1"
        );
        setStats(data);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Gagal memuat data dashboard."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <p className="text-red-600 mb-2">{error || "Data tidak tersedia"}</p>
        <p className="text-sm text-gray-500">
          Coba refresh halaman atau hubungi admin.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Karyawan"
          value={stats.total_employees}
          icon={<Users className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Payroll Aktif"
          value={stats.active_payroll_runs}
          icon={<Banknote className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Lembur Pending"
          value={stats.pending_overtime}
          icon={<Clock className="w-6 h-6" />}
          color="amber"
        />
        <StatCard
          title="Total Payroll Bulan Ini"
          value={`Rp ${stats.total_payroll_this_month.toLocaleString("id-ID")}`}
          icon={<TrendingUp className="w-6 h-6" />}
          color="blue"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <PayrollSummaryChart data={stats.monthly_trend} />
        <EmployeeChart data={stats.employees_by_department} />
      </div>

      <RecentActivity />
    </div>
  );
}
