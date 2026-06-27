'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Eye, Check, Play, AlertTriangle, RefreshCw, X, Loader2, Users } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { formatIDR, getMonthName } from '@/lib/utils';
import Button from '@/components/ui/Button';

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
  created_by: number | null;
  approved_by: number | null;
  approval_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

type PayrollStatus = 'ALL' | 'DRAFT' | 'PROCESSING' | 'COMPLETED' | 'APPROVED' | 'PAID';

const STATUS_OPTIONS: { value: PayrollStatus; label: string }[] = [
  { value: 'ALL', label: 'Semua' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'PROCESSING', label: 'Processing' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'PAID', label: 'Paid' },
];

const STATUS_BADGE: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-700',
  PROCESSING: 'bg-yellow-100 text-yellow-700',
  COMPLETED: 'bg-blue-100 text-blue-700',
  APPROVED: 'bg-green-100 text-green-700',
  PAID: 'bg-purple-100 text-purple-700',
};

const CURRENT_YEAR = new Date().getFullYear();
const CURRENT_MONTH = new Date().getMonth() + 1;

const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - 4 + i);
const MONTH_OPTIONS = [
  { value: 0, label: 'Semua Bulan' },
  { value: 1, label: 'Januari' },
  { value: 2, label: 'Februari' },
  { value: 3, label: 'Maret' },
  { value: 4, label: 'April' },
  { value: 5, label: 'Mei' },
  { value: 6, label: 'Juni' },
  { value: 7, label: 'Juli' },
  { value: 8, label: 'Agustus' },
  { value: 9, label: 'September' },
  { value: 10, label: 'Oktober' },
  { value: 11, label: 'November' },
  { value: 12, label: 'Desember' },
];

export default function PayrollPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<PayrollRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<PayrollStatus>('ALL');
  const [yearFilter, setYearFilter] = useState<number>(CURRENT_YEAR);
  const [monthFilter, setMonthFilter] = useState<number>(0);
  const [approving, setApproving] = useState<number | null>(null);
  const [processing, setProcessing] = useState<number | null>(null);

  // Batch processing state
  const [processingRunId, setProcessingRunId] = useState<number | null>(null);
  const [processProgress, setProcessProgress] = useState({
    current: 0,
    total: 0,
    message: '',
  });
  const [processError, setProcessError] = useState<string | null>(null);

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [eligibleCount, setEligibleCount] = useState<number | null>(null);
  const [createForm, setCreateForm] = useState({
    payroll_period: `${CURRENT_YEAR}-${String(CURRENT_MONTH).padStart(2, '0')}`,
    payroll_method: '',
    tax_method: 'PASAL_17',
    notes: '',
  });

  const fetchEligibleCount = async (period: string) => {
    const [year, month] = period.split('-').map(Number);
    const start = `${year}-${String(month).padStart(2, '0')}-01`;
    const end = new Date(year, month, 0).toISOString().split('T')[0];
    try {
      const count = await api.get<number>(
        `/api/v1/payroll/preview/eligible-count?company_id=1&period_start=${start}&period_end=${end}`
      );
      setEligibleCount(count);
    } catch {
      setEligibleCount(null);
    }
  };

  useEffect(() => {
    fetchEligibleCount(createForm.payroll_period);
  }, []);

  const fetchRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<PayrollRun[]>(
        `/api/v1/payroll/runs?company_id=1&skip=0&limit=100`
      );
      setRuns(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Tidak dapat memuat data. Pastikan server backend berjalan.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleApprove = async (runId: number) => {
    setApproving(runId);
    try {
      await api.post(`/api/v1/payroll/runs/${runId}/approve`, { approved_by: 1 });
      await fetchRuns();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menyetujui payroll run.');
    } finally {
      setApproving(null);
    }
  };

  const handleProcess = async (run: PayrollRun) => {
    setProcessing(run.id);
    setProcessingRunId(run.id);
    setProcessError(null);
    setProcessProgress({ current: 0, total: 0, message: 'Mempersiapkan...' });

    try {
      const [year, month] = run.payroll_period.split('-').map(Number);
      const start = `${year}-${String(month).padStart(2, '0')}-01`;
      const end = new Date(year, month, 0).toISOString().split('T')[0];

      // Fetch eligible employee IDs
      const ids = await api.get<number[]>(
        `/api/v1/payroll/preview/eligible-ids?company_id=${run.company_id}&period_start=${start}&period_end=${end}`
      );

      if (ids.length === 0) {
        setProcessError('Tidak ada karyawan eligible untuk diproses.');
        setProcessing(null);
        return;
      }

      setProcessProgress({ current: 0, total: ids.length, message: `Memproses 0/${ids.length} karyawan...` });

      const batchSize = 25;
      for (let i = 0; i < ids.length; i += batchSize) {
        const batch = ids.slice(i, i + batchSize);
        const isLast = i + batchSize >= ids.length;

        setProcessProgress({
          current: i,
          total: ids.length,
          message: `Memproses ${i + 1}-${Math.min(i + batchSize, ids.length)} dari ${ids.length} karyawan...`,
        });

        await api.post(`/api/v1/payroll/runs/${run.id}/process-batch`, {
          employee_ids: batch,
          finalize: isLast,
        });

        setProcessProgress({
          current: Math.min(i + batchSize, ids.length),
          total: ids.length,
          message: `Selesai ${Math.min(i + batchSize, ids.length)}/${ids.length} karyawan...`,
        });
      }

      await fetchRuns();
      setProcessingRunId(null);
      router.push(`/payroll/${run.id}`);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Gagal memproses payroll.';
      setProcessError(msg);
      alert(msg);
    } finally {
      setProcessing(null);
    }
  };

  const filteredRuns = runs.filter((run) => {
    if (statusFilter !== 'ALL' && run.status !== statusFilter) return false;
    const [year, month] = run.payroll_period.split('-').map(Number);
    if (yearFilter && year !== yearFilter) return false;
    if (monthFilter > 0 && month !== monthFilter) return false;
    return true;
  });

  const formatPeriod = (period: string) => {
    const [year, month] = period.split('-').map(Number);
    return `${getMonthName(month)} ${year}`;
  };

  const getPeriodDates = (period: string) => {
    const [year, month] = period.split('-').map(Number);
    const start = new Date(year, month - 1, 1);
    const end = new Date(year, month, 0);
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    };
  };

  const handleCreate = async () => {
    setCreating(true);
    setCreateError(null);
    try {
      const dates = getPeriodDates(createForm.payroll_period);
      const body: Record<string, unknown> = {
        company_id: 1,
        payroll_period: createForm.payroll_period,
        period_start_date: dates.start,
        period_end_date: dates.end,
        tax_method: createForm.tax_method,
      };
      if (createForm.payroll_method) {
        body.payroll_method = createForm.payroll_method;
      }
      if (createForm.notes.trim()) {
        body.notes = createForm.notes.trim();
      }
      await api.post('/api/v1/payroll/runs?created_by=1', body);
      setShowCreateModal(false);
      setCreateForm({
        payroll_period: `${CURRENT_YEAR}-${String(CURRENT_MONTH).padStart(2, '0')}`,
        payroll_method: '',
        tax_method: 'PASAL_17',
        notes: '',
      });
      fetchRuns();
    } catch (err) {
      if (err instanceof ApiError) {
        setCreateError(err.message);
      } else {
        setCreateError('Gagal membuat payroll. Pastikan backend berjalan.');
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Payroll</h1>
          <p className="text-sm text-gray-500 mt-1">
            Kelola proses payroll perusahaan
          </p>
        </div>
        <Button onClick={() => { setShowCreateModal(true); setCreateError(null); fetchEligibleCount(createForm.payroll_period); }}>
          <Plus className="w-4 h-4 mr-2" />
          Buat Payroll Baru
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as PayrollStatus)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            {YEAR_OPTIONS.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>

          <select
            value={monthFilter}
            onChange={(e) => setMonthFilter(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            {MONTH_OPTIONS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4 mx-auto" />
            <div className="h-48 bg-gray-200 rounded" />
          </div>
        </div>
      ) : error ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <p className="text-gray-700 mb-4">{error}</p>
          <Button variant="secondary" onClick={fetchRuns}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Coba Lagi
          </Button>
        </div>
      ) : filteredRuns.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Plus className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Belum ada data payroll
          </h3>
          <p className="text-sm text-gray-500">
            Buat payroll baru untuk memulai.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Periode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Metode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Jumlah Karyawan
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Gaji Kotor
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Gaji Bersih
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Aksi
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatPeriod(run.payroll_period)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {run.payroll_method}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[run.status] || 'bg-gray-100 text-gray-700'}`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {run.total_employees}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-mono">
                      {formatIDR(run.total_gross)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-mono">
                      {formatIDR(run.total_net)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          title="Lihat Detail"
                          onClick={() => router.push(`/payroll/${run.id}`)}
                          className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {run.status === 'DRAFT' && (
                          <button
                            title="Proses Gaji"
                            onClick={() => handleProcess(run)}
                            disabled={processing === run.id}
                            className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                          >
                            {processing === run.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                          </button>
                        )}
                        {run.status === 'COMPLETED' && (
                          <button
                            title="Approve"
                            onClick={() => handleApprove(run.id)}
                            disabled={approving === run.id}
                            className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Payroll Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowCreateModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Buat Payroll Baru</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Periode Payroll</label>
                <input
                  type="text"
                  value={createForm.payroll_period}
                  onChange={(e) => {
                    const v = e.target.value;
                    setCreateForm({ ...createForm, payroll_period: v });
                    if (/^\d{4}-\d{2}$/.test(v)) fetchEligibleCount(v);
                  }}
                  placeholder="YYYY-MM"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <p className="text-xs text-gray-500 mt-1">Format: YYYY-MM (contoh: 2026-06)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Metode Penggajian</label>
                <select
                  value={createForm.payroll_method}
                  onChange={(e) => setCreateForm({ ...createForm, payroll_method: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Default dari pengaturan PPh 21</option>
                  <option value="GROSS">Gross (pajak ditanggung karyawan)</option>
                  <option value="GROSS_UP">Gross Up (tunjangan pajak)</option>
                  <option value="NETT">Nett (pajak ditanggung perusahaan)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Metode PPh 21</label>
                <select
                  value={createForm.tax_method}
                  onChange={(e) => setCreateForm({ ...createForm, tax_method: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="PASAL_17">Pasal 17 (Progresif)</option>
                  <option value="TER">TER (Tarif Efektif Rata-rata)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Catatan (opsional)</label>
                <textarea
                  value={createForm.notes}
                  onChange={(e) => setCreateForm({ ...createForm, notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              {eligibleCount !== null && (
                <div className="flex items-center gap-2 p-3 bg-primary-50 border border-primary-200 rounded-lg">
                  <Users className="w-4 h-4 text-primary-600" />
                  <div>
                    <p className="text-sm font-medium text-primary-800">
                      {eligibleCount} karyawan eligible
                    </p>
                    <p className="text-xs text-primary-700">
                      Hanya karyawan dengan tanggal masuk ≤ tanggal 15 bulan ini yang akan diproses
                    </p>
                  </div>
                </div>
              )}
            </div>

            {createError && (
              <div className="mt-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {createError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleCreate}
                disabled={creating}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating && <Loader2 className="w-4 h-4 animate-spin" />}
                Buat
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Processing Progress Modal */}
      {processingRunId !== null && (
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
