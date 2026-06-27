'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Pencil,
  Trash2,
  X,
  Loader2,
  AlertCircle,
  RefreshCw,
  Check,
  XCircle,
  Banknote,
  Eye,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { formatIDR } from '@/lib/utils';
import { PaginatedResponse } from '@/types';
import { EmployeeSearchSelect } from '@/components/employees/EmployeeSearchSelect';
import { ExcelActions } from '@/components/ui/ExcelActions';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Employee {
  id: number;
  first_name: string;
  last_name: string | null;
  employee_code: string;
}

interface Installment {
  id: number;
  installment_number: number;
  amount: string;
  due_date: string;
  is_paid: boolean;
  paid_date: string | null;
  payroll_run_id: number | null;
}

interface Kasbon {
  id: number;
  employee_id: number;
  employee_name: string;
  kasbon_number: string;
  principal_amount: string;
  interest_rate: string;
  interest_amount: string;
  total_amount: string;
  purpose: string;
  request_date: string;
  approval_date: string | null;
  disbursement_date: string | null;
  number_of_installments: number;
  installment_amount: string;
  status: 'PENDING' | 'APPROVED' | 'DISBURSED' | 'COMPLETED' | 'REJECTED';
  approved_by: number | null;
  notes: string | null;
  total_paid: string;
  remaining_balance: string;
  installments: Installment[];
}

interface KasbonFormData {
  employee_id: string;
  kasbon_number: string;
  principal_amount: string;
  interest_rate: string;
  purpose: string;
  request_date: string;
  number_of_installments: string;
  installment_amount: string;
  notes: string;
}

const EMPTY_KASBON_FORM: KasbonFormData = {
  employee_id: '',
  kasbon_number: '',
  principal_amount: '',
  interest_rate: '0',
  purpose: '',
  request_date: '',
  number_of_installments: '1',
  installment_amount: '',
  notes: '',
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function KasbonPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [kasbonList, setKasbonList] = useState<Kasbon[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showModal, setShowModal] = useState(false);
  const [editingKasbon, setEditingKasbon] = useState<Kasbon | null>(null);
  const [form, setForm] = useState<KasbonFormData>(EMPTY_KASBON_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Kasbon | null>(null);
  const [detailKasbon, setDetailKasbon] = useState<Kasbon | null>(null);

  // ─── Data Fetching ──────────────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [empData, kasbonData] = await Promise.all([
        api.get<PaginatedResponse<Employee>>('/api/v1/employees?company_id=1&skip=0&limit=1000'),
        api.get<Kasbon[]>('/api/v1/kasbon?company_id=1'),
      ]);
      setEmployees(empData.items);
      setKasbonList(kasbonData);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Tidak dapat terhubung ke server.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ─── Helpers ────────────────────────────────────────────────────────────────

  const generateKasbonNumber = () => {
    const now = new Date();
    const seq = String(kasbonList.length + 1).padStart(4, '0');
    return `KSB-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}-${seq}`;
  };

  const recalcInstallment = (
    principal: string,
    interestRate: string,
    installments: string
  ): string => {
    const p = Number(principal) || 0;
    const rate = Number(interestRate) || 0;
    const n = Number(installments) || 1;
    if (n <= 0) return '';
    const total = p * (1 + rate / 100);
    return String(Math.round(total / n));
  };

  // ─── Handlers ───────────────────────────────────────────────────────────────

  const openAddModal = () => {
    setEditingKasbon(null);
    setForm({
      ...EMPTY_KASBON_FORM,
      kasbon_number: generateKasbonNumber(),
      request_date: new Date().toISOString().split('T')[0],
    });
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (item: Kasbon) => {
    setEditingKasbon(item);
    setForm({
      employee_id: String(item.employee_id),
      kasbon_number: item.kasbon_number,
      principal_amount: item.principal_amount,
      interest_rate: item.interest_rate || '0',
      purpose: item.purpose,
      request_date: item.request_date,
      number_of_installments: String(item.number_of_installments),
      installment_amount: item.installment_amount,
      notes: item.notes || '',
    });
    setFormError(null);
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);
    try {
      const body = {
        employee_id: Number(form.employee_id),
        kasbon_number: form.kasbon_number,
        principal_amount: Number(form.principal_amount),
        interest_rate: Number(form.interest_rate),
        purpose: form.purpose,
        request_date: form.request_date,
        number_of_installments: Number(form.number_of_installments),
        installment_amount: Number(form.installment_amount),
        notes: form.notes || null,
      };
      if (editingKasbon) {
        await api.patch(`/api/v1/kasbon/${editingKasbon.id}`, body);
      } else {
        await api.post('/api/v1/kasbon', body);
      }
      setShowModal(false);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(err.message);
      } else {
        setFormError('Terjadi kesalahan. Coba lagi.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/api/v1/kasbon/${deleteTarget.id}`);
      setDeleteTarget(null);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    }
  };

  const handleStatusChange = async (
    kasbon: Kasbon,
    status: 'APPROVED' | 'REJECTED' | 'DISBURSED' | 'COMPLETED'
  ) => {
    try {
      await api.patch(`/api/v1/kasbon/${kasbon.id}/status`, {
        status,
        approved_by: 1,
      });
      fetchData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal mengubah status pinjaman.');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'bg-blue-100 text-blue-700';
      case 'DISBURSED':
        return 'bg-emerald-100 text-emerald-700';
      case 'COMPLETED':
        return 'bg-gray-100 text-gray-700';
      case 'REJECTED':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-yellow-100 text-yellow-700';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'Menunggu';
      case 'APPROVED':
        return 'Disetujui';
      case 'DISBURSED':
        return 'Dicairkan';
      case 'COMPLETED':
        return 'Lunas';
      case 'REJECTED':
        return 'Ditolak';
      default:
        return status;
    }
  };

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pinjaman Karyawan (Kasbon)</h1>
          <p className="text-sm text-gray-500 mt-1">
            Kelola pinjaman karyawan dan jadwal cicilan yang dipotong dari gaji
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <ExcelActions module="kasbon" companyId={1} onImportSuccess={fetchData} />
          <button
            onClick={openAddModal}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Tambah Pinjaman
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
          <span className="ml-2 text-sm text-gray-500">Memuat data...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12 bg-white rounded-xl border border-gray-200">
          <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
          <p className="text-sm text-gray-600 mb-3">{error}</p>
          <button
            onClick={fetchData}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-indigo-600 border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Coba Lagi
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-500">No. Pinjaman</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Karyawan</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Pinjaman Pokok</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Bunga</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Total Pinjaman</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Cicilan/Bulan</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Tenor</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Sisa</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {kasbonList.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="text-center py-12 text-gray-500">
                      Belum ada data pinjaman.
                    </td>
                  </tr>
                ) : (
                  kasbonList.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 font-mono text-gray-900">{item.kasbon_number}</td>
                      <td className="py-3 px-4 text-gray-900">{item.employee_name}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatIDR(Number(item.principal_amount))}</td>
                      <td className="py-3 px-4 text-right font-mono text-blue-600">{Number(item.interest_rate || 0).toFixed(2)}%</td>
                      <td className="py-3 px-4 text-right font-mono">{formatIDR(Number(item.total_amount))}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatIDR(Number(item.installment_amount))}</td>
                      <td className="py-3 px-4 text-gray-600">{item.number_of_installments}x</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(item.status)}`}>
                          {getStatusLabel(item.status)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono">
                        {item.status === 'DISBURSED' || item.status === 'COMPLETED'
                          ? formatIDR(Number(item.remaining_balance))
                          : '-'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => setDetailKasbon(item)}
                            className="p-1.5 rounded-md hover:bg-indigo-50 text-slate-500 hover:text-indigo-600 transition-colors"
                            title="Lihat Detail"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {item.status === 'PENDING' && (
                            <>
                              <button
                                onClick={() => handleStatusChange(item, 'APPROVED')}
                                className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                                title="Setujui"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleStatusChange(item, 'REJECTED')}
                                className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-red-600 transition-colors"
                                title="Tolak"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          {item.status === 'APPROVED' && (
                            <button
                              onClick={() => handleStatusChange(item, 'DISBURSED')}
                              className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                              title="Cairkan"
                            >
                              <Banknote className="w-4 h-4" />
                            </button>
                          )}
                          {item.status === 'DISBURSED' && (
                            <button
                              onClick={() => handleStatusChange(item, 'COMPLETED')}
                              className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                              title="Tandai Lunas"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                          {(item.status === 'PENDING' || item.status === 'APPROVED' || item.status === 'REJECTED') && (
                            <>
                              <button
                                onClick={() => openEditModal(item)}
                                className="p-1.5 rounded-md hover:bg-indigo-50 text-slate-500 hover:text-indigo-600 transition-colors"
                                title="Edit"
                              >
                                <Pencil className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setDeleteTarget(item)}
                                className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-red-600 transition-colors"
                                title="Hapus"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── Kasbon Modal ────────────────────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowModal(false)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingKasbon ? 'Edit' : 'Tambah'} Pinjaman
              </h3>
              <button onClick={() => setShowModal(false)} className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <EmployeeSearchSelect
                employees={employees}
                value={form.employee_id}
                onChange={(value) => setForm({ ...form, employee_id: value })}
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">No. Pinjaman</label>
                <input
                  type="text"
                  value={form.kasbon_number}
                  onChange={(e) => setForm({ ...form, kasbon_number: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Contoh: KSB-202601-0001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jumlah Pinjaman</label>
                <input
                  type="number"
                  value={form.principal_amount}
                  onChange={(e) => {
                    const principal = e.target.value;
                    const installment = recalcInstallment(principal, form.interest_rate, form.number_of_installments);
                    setForm({ ...form, principal_amount: principal, installment_amount: installment });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Contoh: 5000000"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Bunga (%)</label>
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    value={form.interest_rate}
                    onChange={(e) => {
                      const rate = e.target.value;
                      const installment = recalcInstallment(form.principal_amount, rate, form.number_of_installments);
                      setForm({ ...form, interest_rate: rate, installment_amount: installment });
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tenor (bulan)</label>
                  <input
                    type="number"
                    min={1}
                    value={form.number_of_installments}
                    onChange={(e) => {
                      const installments = e.target.value;
                      const installment = recalcInstallment(form.principal_amount, form.interest_rate, installments);
                      setForm({ ...form, number_of_installments: installments, installment_amount: installment });
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cicilan/Bulan</label>
                <input
                  type="number"
                  value={form.installment_amount}
                  onChange={(e) => setForm({ ...form, installment_amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tanggal Pengajuan</label>
                <input
                  type="date"
                  value={form.request_date}
                  onChange={(e) => setForm({ ...form, request_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tujuan Pinjaman</label>
                <textarea
                  value={form.purpose}
                  onChange={(e) => setForm({ ...form, purpose: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Contoh: Biaya pendidikan anak"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Catatan</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>

            {formError && (
              <div className="mt-3 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {formError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Detail Modal ────────────────────────────────────────────────────── */}
      {detailKasbon && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setDetailKasbon(null)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Detail Pinjaman</h3>
              <button onClick={() => setDetailKasbon(null)} className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <p className="text-xs text-gray-500">No. Pinjaman</p>
                <p className="text-sm font-medium text-gray-900">{detailKasbon.kasbon_number}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Karyawan</p>
                <p className="text-sm font-medium text-gray-900">{detailKasbon.employee_name}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Pinjaman Pokok</p>
                <p className="text-sm font-medium text-gray-900">{formatIDR(Number(detailKasbon.principal_amount))}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Bunga</p>
                <p className="text-sm font-medium text-gray-900">{Number(detailKasbon.interest_rate || 0).toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Total Pinjaman</p>
                <p className="text-sm font-medium text-gray-900">{formatIDR(Number(detailKasbon.total_amount))}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Cicilan/Bulan</p>
                <p className="text-sm font-medium text-gray-900">{formatIDR(Number(detailKasbon.installment_amount))}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Status</p>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(detailKasbon.status)}`}>
                  {getStatusLabel(detailKasbon.status)}
                </span>
              </div>
              <div>
                <p className="text-xs text-gray-500">Sisa Pinjaman</p>
                <p className="text-sm font-medium text-gray-900">{formatIDR(Number(detailKasbon.remaining_balance))}</p>
              </div>
            </div>

            <h4 className="text-sm font-semibold text-gray-900 mb-3">Jadwal Cicilan</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left py-2 px-3 font-medium text-gray-500">Ke-</th>
                    <th className="text-right py-2 px-3 font-medium text-gray-500">Jumlah</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-500">Jatuh Tempo</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {detailKasbon.installments.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="text-center py-8 text-gray-500">
                        Belum ada jadwal cicilan (pinjaman belum dicairkan).
                      </td>
                    </tr>
                  ) : (
                    detailKasbon.installments.map((inst) => (
                      <tr key={inst.id}>
                        <td className="py-2 px-3 text-gray-900">{inst.installment_number}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatIDR(Number(inst.amount))}</td>
                        <td className="py-2 px-3 text-gray-600">{inst.due_date}</td>
                        <td className="py-2 px-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${inst.is_paid ? 'bg-emerald-100 text-emerald-700' : 'bg-yellow-100 text-yellow-700'}`}>
                            {inst.is_paid ? 'Lunas' : 'Belum'}
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
      )}

      {/* ─── Delete Confirmation ─────────────────────────────────────────────── */}
      {deleteTarget && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/30" onClick={() => setDeleteTarget(null)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-red-100 p-6 w-full max-w-sm mx-4">
            <h4 className="text-base font-semibold text-gray-900 mb-2">Konfirmasi Hapus</h4>
            <p className="text-sm text-gray-600 mb-4">
              Hapus pinjaman <span className="font-semibold">{deleteTarget.kasbon_number}</span>?
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleDelete}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                Hapus
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
