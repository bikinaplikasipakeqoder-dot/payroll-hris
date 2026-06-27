"use client";

import { Users, Banknote, Clock, TrendingUp } from "lucide-react";
import StatCard from "@/components/dashboard/StatCard";
import PayrollSummaryChart from "@/components/dashboard/PayrollSummaryChart";
import EmployeeChart from "@/components/dashboard/EmployeeChart";
import RecentActivity from "@/components/dashboard/RecentActivity";

export default function DashboardPage() {
  // TODO: Wire to real API using api.get<DashboardStats>('/dashboard/stats')
  const stats = {
    totalEmployees: 115,
    activePayrollRuns: 2,
    pendingOvertimeApprovals: 8,
    totalPayrollThisMonth: 535000000,
  };

  return (
    <div>
      {/* Page heading */}
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Dashboard</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Karyawan"
          value={stats.totalEmployees}
          icon={<Users className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Payroll Aktif"
          value={stats.activePayrollRuns}
          icon={<Banknote className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Lembur Pending"
          value={stats.pendingOvertimeApprovals}
          icon={<Clock className="w-6 h-6" />}
          color="amber"
        />
        <StatCard
          title="Total Payroll Bulan Ini"
          value={`Rp ${stats.totalPayrollThisMonth.toLocaleString("id-ID")}`}
          icon={<TrendingUp className="w-6 h-6" />}
          color="blue"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <PayrollSummaryChart />
        <EmployeeChart />
      </div>

      {/* Recent Activity */}
      <RecentActivity />
    </div>
  );
}
