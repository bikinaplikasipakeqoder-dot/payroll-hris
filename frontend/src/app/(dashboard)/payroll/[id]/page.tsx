'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Loader2,
  AlertTriangle,
  RefreshCw,
  Check,
  FileText,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { formatIDR, getMonthName } from '@/lib/utils';
import { PaginatedResponse } from '@/types';
import { processPayrollInBatches } from '@/lib/payroll-batch';
import Button from '@/components/ui/Button';

// ─── Types ───────────────────────────────────────────────────────────────────

interface PayrollRun {
  id: number;
  company_id: number;
  payroll_period: string;
  period_start_date: string;
  period_end_date: string;
  payroll_method: string;
  tax_method: string;
  status: string;
  total_employees: number;
  total_gross: number;
  total_deductions: number;
  total_tax: number;
  total_net: number;
  notes: string | null;
  created_at: string;
}

interface Payslip {
  id: number;
  employee_id: number;
  payslip_number: string;
  basic_salary: number;
  total_allowances: number;
  overtime_amount: number;
  bonus_amount: number;
  gross_salary: number;
  bpjs_kes_employee: number;
  bpjs_jht_employee: number;
  bpjs_jp_employee: number;
  pph21_tax: number;
  kasbon_deduction: number;
  other_deductions: number;
  total_deductions: number;
  net_salary: number;
  tax_allowance: number;
  working_days: number;
  overtime_hours: number;
  late_minutes: number;
  sick_days: number;
  leave_days: number;
  is_approved: boolean;
  lines: PayslipLine[];
}

interface PayslipLine {
  id: number;
  line_type: 'EARNING' | 'DEDUCTION' | 'TAX' | 'BPJS' | 'NET';
  category: string | null;
  description: string;
  amount: number;
  sort_order: number;
}

interface Employee {
  id: number;
  first_name: string;
  last_name: string | null;
  employee_code: string;
}

const STATUS_BADGE: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-700',
  PROCESSING: 'bg-yellow-100 text-yellow-700',
  COMPLETED: 'bg-blue-100 text-blue-700',
  APPROVED: 'bg-green-100 text-green-700',
  PAID: 'bg-purple-100 text-purple-700',
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function PayrollDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = Number(params.id);

  const [run, setRun] = useState<PayrollRun | null>(null);
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [approving, setApproving] = useState(false);
  const [processProgress, setProcessProgress] = useState({
    current: 0,
    total: 0,
    message: '',
  });
  const [processError, setProcessError] = useState<string | null>(null);
  const [expandedPayslipId, setExpandedPayslipId] = useState<number | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [runData, payslipData, employeeData] = await Promise.all([
        api.get<PayrollRun>(`/api/v1/payroll/runs/${runId}`),
        api.get<Payslip[]>(`/api/v1/payroll/runs/${runId}/payslips?limit=1000`),
        api.get<PaginatedResponse<Employee>>('/api/v1/employees?company_id=1&skip=0&limit=1000'),
      ]);
      setRun(runData);
      setPayslips(payslipData);
      setEmployees(employeeData.items);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Tidak dapat memuat data payroll.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (runId) fetchData();
  }, [runId]);

  const handleProcess = async () => {
    if (!run) return;
    setProcessing(true);
    setProcessError(null);

    await processPayrollInBatches(run, {
      onProgress: (progress) => setProcessProgress(progress),
      onError: (msg) => {
        setProcessError(msg);
        alert(msg);
      },
      onComplete: () => {
        fetchData();
      },
    });

    setProcessing(false);
  };

  const handleApprove = async () => {
    setApproving(true);
    try {
      await api.post(`/api/v1/payroll/runs/${runId}/approve`, { approved_by: 1 });
      fetchData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menyetujui payroll.');
    } finally {
      setApproving(false);
    }
  };

  const toggleExpanded = (payslipId: number) => {
    setExpandedPayslipId((current) => (current === payslipId ? null : payslipId));
  };

  const getEmployeeName = (employeeId: number) => {
    const emp = employees.find((e) => e.id === employeeId);
    if (!emp) return `Karyawan #${employeeId}`;
    return `${emp.first_name} ${emp.last_name || ''}`.trim();
  };

  const formatPeriod = (period: string) => {
    const [year, month] = period.split('-').map(Number);
    return `${getMonthName(month)} ${year}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
        <span className="ml-3 text-slate-600">Memuat data payroll...</span>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
        <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
        <p className="text-gray-700 mb-4">{error || 'Data payroll tidak ditemukan.'}</p>
        <Button variant="secondary" onClick={fetchData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Coba Lagi
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/payroll')}
            className="p-2 rounded-lg hover:bg-gray-100 text-slate-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Payroll {formatPeriod(run.payroll_period)}
            </h1>
            <p className="text-sm text-gray-500">
              Periode {run.period_start_date} s/d {run.period_end_date}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_BADGE[run.status] || 'bg-gray-100 text-gray-700'}`}>
            {run.status}
          </span>
          {run.status === 'DRAFT' && (
            <Button onClick={handleProcess} disabled={processing}>
              {processing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              Proses Gaji
            </Button>
          )}
          {run.status === 'COMPLETED' && (
            <Button onClick={handleApprove} disabled={approving}>
              {approving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Check className="w-4 h-4 mr-2" />}
              Approve
            </Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard label="Jumlah Karyawan" value={String(run.total_employees)} />
        <SummaryCard label="Total Gaji Kotor" value={formatIDR(run.total_gross)} />
        <SummaryCard label="Total Potongan" value={formatIDR(run.total_deductions)} />
        <SummaryCard label="Total Gaji Bersih" value={formatIDR(run.total_net)} highlight />
      </div>

      {/* Payslips Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Rincian Gaji per Karyawan</h2>
          <p className="text-sm text-gray-500">Take home pay dan komponen gaji masing-masing karyawan</p>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Karyawan</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider">Gaji Pokok</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider">Tunjangan</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider">Lembur</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider">Bonus</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider">Bruto</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider">BPJS + PPh21</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider">Take Home Pay</th>
                <th className="px-4 py-3 text-center font-medium text-gray-500 uppercase tracking-wider">Aksi</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {payslips.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-gray-500">
                    {run.status === 'DRAFT'
                      ? 'Payroll belum diproses. Klik "Proses Gaji" untuk menghitung gaji karyawan.'
                      : 'Tidak ada data payslip.'}
                  </td>
                </tr>
              ) : (
                payslips.map((payslip) => {
                  const isExpanded = expandedPayslipId === payslip.id;
                  return (
                    <>
                      <tr
                        key={payslip.id}
                        className="hover:bg-gray-50 transition-colors cursor-pointer"
                        onClick={() => toggleExpanded(payslip.id)}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4 text-gray-400" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-gray-400" />
                            )}
                            <div>
                              <div className="font-medium text-gray-900">{getEmployeeName(payslip.employee_id)}</div>
                              <div className="text-xs text-gray-500">{payslip.payslip_number}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right font-mono">{formatIDR(payslip.basic_salary)}</td>
                        <td className="px-4 py-3 text-right font-mono">{formatIDR(payslip.total_allowances)}</td>
                        <td className="px-4 py-3 text-right font-mono">{formatIDR(payslip.overtime_amount)}</td>
                        <td className="px-4 py-3 text-right font-mono">{formatIDR(payslip.bonus_amount)}</td>
                        <td className="px-4 py-3 text-right font-mono">{formatIDR(payslip.gross_salary)}</td>
                        <td className="px-4 py-3 text-right font-mono">{formatIDR(payslip.total_deductions)}</td>
                        <td className="px-4 py-3 text-right font-mono font-semibold text-emerald-700">{formatIDR(payslip.net_salary)}</td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/payslips/${run.payroll_period}?payslip_id=${payslip.id}`);
                            }}
                            className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                            title="Lihat Slip Gaji"
                          >
                            <FileText className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={9} className="bg-slate-50 px-4 py-4">
                            <PayslipBreakdown payslip={payslip} />
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Batch Processing Progress Modal */}
      {processing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Memproses Payroll</h3>
              <p className="text-sm text-gray-500 mt-1">
                Mohon tunggu, payroll diproses per batch agar tidak timeout.
              </p>
            </div>

            <div className="mb-2 flex justify-between text-sm text-gray-600">
              <span>{processProgress.message}</span>
              <span>{processProgress.current}/{processProgress.total}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{
                  width: processProgress.total > 0
                    ? `${Math.round((processProgress.current / processProgress.total) * 100)}%`
                    : '0%',
                }}
              />
            </div>

            {processError && (
              <div className="mt-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {processError}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Reusable Summary Card ───────────────────────────────────────────────────

function PayslipBreakdown({ payslip }: { payslip: Payslip }) {
  const lines = payslip.lines || [];

  const earnings = lines.filter((l) => l.line_type === 'EARNING');
  const employeeBpjs = lines.filter(
    (l) => l.line_type === 'BPJS' && !l.category?.startsWith('EMPLOYER_') && l.category !== 'JKK' && l.category !== 'JKM'
  );
  const employerBpjs = lines.filter(
    (l) => l.line_type === 'BPJS' && (l.category?.startsWith('EMPLOYER_') || l.category === 'JKK' || l.category === 'JKM')
  );
  const taxes = lines.filter((l) => l.line_type === 'TAX');
  const deductions = lines.filter((l) => l.line_type === 'DEDUCTION');
  const netLine = lines.find((l) => l.line_type === 'NET');

  const sum = (items: PayslipLine[]) => items.reduce((acc, item) => acc + Number(item.amount), 0);

  const renderRows = (items: PayslipLine[], negative = false) =>
    items.map((item) => (
      <div key={item.id} className="flex justify-between py-1 text-sm">
        <span className="text-slate-600">{item.description}</span>
        <span className={`font-mono ${negative ? 'text-red-600' : 'text-slate-800'}`}>
          {negative ? '-' : ''}{formatIDR(item.amount)}
        </span>
      </div>
    ));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Left: Earnings */}
      <div className="space-y-4">
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h4 className="font-semibold text-slate-800 mb-3">Pendapatan</h4>
          {renderRows(earnings)}
          <div className="border-t border-slate-200 mt-3 pt-3 flex justify-between font-semibold text-slate-900">
            <span>Bruto</span>
            <span className="font-mono">{formatIDR(payslip.gross_salary)}</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h4 className="font-semibold text-slate-800 mb-3">Informasi Kehadiran</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <InfoRow label="Hari Kerja" value={String(payslip.working_days)} />
            <InfoRow label="Jam Lembur" value={String(payslip.overtime_hours)} />
            <InfoRow label="Menit Terlambat" value={String(payslip.late_minutes)} />
            <InfoRow label="Hari Sakit" value={String(payslip.sick_days)} />
            <InfoRow label="Hari Cuti" value={String(payslip.leave_days)} />
          </div>
        </div>
      </div>

      {/* Right: Deductions */}
      <div className="space-y-4">
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h4 className="font-semibold text-slate-800 mb-3">BPJS (Pemotongan Karyawan)</h4>
          {employeeBpjs.length > 0 ? renderRows(employeeBpjs, true) : (
            <p className="text-sm text-slate-500">Tidak ada pemotongan BPJS.</p>
          )}
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h4 className="font-semibold text-slate-800 mb-3">BPJS (Tanggungan Perusahaan)</h4>
          {employerBpjs.length > 0 ? renderRows(employerBpjs) : (
            <p className="text-sm text-slate-500">Tidak ada data BPJS perusahaan.</p>
          )}
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h4 className="font-semibold text-slate-800 mb-3">Pajak & Potongan Lainnya</h4>
          {renderRows(taxes, true)}
          {renderRows(deductions, true)}
          <div className="border-t border-slate-200 mt-3 pt-3 flex justify-between font-semibold text-red-600">
            <span>Total Potongan</span>
            <span className="font-mono">-{formatIDR(payslip.total_deductions)}</span>
          </div>
        </div>

        <div className="bg-emerald-50 rounded-lg border border-emerald-200 p-4">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-emerald-900">Take Home Pay</span>
            <span className="font-mono font-bold text-emerald-700 text-lg">
              {formatIDR(netLine ? netLine.amount : payslip.net_salary)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800">{value}</span>
    </div>
  );
}

// ─── Reusable Summary Card ───────────────────────────────────────────────────

function SummaryCard({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl p-4 border ${highlight ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-gray-200'}`}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-xl font-bold mt-1 ${highlight ? 'text-emerald-700' : 'text-gray-900'}`}>
        {value}
      </p>
    </div>
  );
}
