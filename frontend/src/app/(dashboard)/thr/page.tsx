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
  Calculator,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { formatIDR } from '@/lib/utils';
import { PaginatedResponse } from '@/types';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Employee {
  id: number;
  first_name: string;
  last_name: string | null;
  employee_code: string;
  religion: string | null;
  base_salary: string;
  join_date: string;
}

interface THRRecord {
  id: number;
  employee_id: number;
  employee_name: string;
  employee_religion: string | null;
  thr_year: number;
  religious_holiday: string;
  amount: string;
  thr_date: string;
  calculation_basis: string;
  tenure_months: number;
  status: 'DRAFT' | 'APPROVED' | 'PAID';
  description: string | null;
}

interface THRFormData {
  employee_id: string;
  thr_year: string;
  religious_holiday: string;
  amount: string;
  thr_date: string;
  description: string;
}

const HOLIDAY_OPTIONS = [
  { value: 'IDUL_FITRI', label: 'Idul Fitri (Muslim)', religionHint: 'Islam' },
  { value: 'CHRISTMAS', label: 'Natal (Kristen/Katolik)', religionHint: 'Kristen/Katolik' },
  { value: 'NYEPI', label: 'Nyepi (Hindu)', religionHint: 'Hindu' },
  { value: 'WAISAK', label: 'Waisak (Buddha)', religionHint: 'Buddha' },
];

const EMPTY_FORM: THRFormData = {
  employee_id: '',
  thr_year: String(new Date().getFullYear()),
  religious_holiday: 'IDUL_FITRI',
  amount: '',
  thr_date: '',
  description: '',
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function THRPage() {
  const [records, setRecords] = useState<THRRecord[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showModal, setShowModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState<THRRecord | null>(null);
  const [formData, setFormData] = useState<THRFormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<THRRecord | null>(null);
  const [calculating, setCalculating] = useState(false);

  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [selectedHoliday, setSelectedHoliday] = useState<string>('IDUL_FITRI');

  // ─── Data Fetching ──────────────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [recordsData, empData] = await Promise.all([
        api.get<THRRecord[]>(`/api/v1/thr?company_id=1&thr_year=${selectedYear}&religious_holiday=${selectedHoliday}`),
        api.get<PaginatedResponse<Employee>>('/api/v1/employees?company_id=1&skip=0&limit=1000'),
      ]);
      setRecords(recordsData);
      setEmployees(empData.items);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Tidak dapat terhubung ke server.');
      }
    } finally {
      setLoading(false);
    }
  }, [selectedYear, selectedHoliday]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ─── Handlers ───────────────────────────────────────────────────────────────

  const openAddModal = () => {
    setEditingRecord(null);
    setFormData({
      ...EMPTY_FORM,
      thr_year: String(selectedYear),
      religious_holiday: selectedHoliday,
    });
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (record: THRRecord) => {
    setEditingRecord(record);
    setFormData({
      employee_id: String(record.employee_id),
      thr_year: String(record.thr_year),
      religious_holiday: record.religious_holiday,
      amount: record.amount,
      thr_date: record.thr_date,
      description: record.description || '',
    });
    setFormError(null);
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);
    try {
      const body = {
        employee_id: Number(formData.employee_id),
        thr_year: Number(formData.thr_year),
        religious_holiday: formData.religious_holiday,
        amount: Number(formData.amount),
        thr_date: formData.thr_date,
        description: formData.description || null,
      };
      if (editingRecord) {
        await api.patch(`/api/v1/thr/${editingRecord.id}`, body);
      } else {
        await api.post('/api/v1/thr', body);
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
      await api.delete(`/api/v1/thr/${deleteTarget.id}`);
      setDeleteTarget(null);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    }
  };

  const handleCalculate = async () => {
    setCalculating(true);
    try {
      await api.post('/api/v1/thr/calculate', {
        company_id: 1,
        thr_year: selectedYear,
        religious_holiday: selectedHoliday,
        reference_date: new Date().toISOString().split('T')[0],
      });
      fetchData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menghitung THR.');
    } finally {
      setCalculating(false);
    }
  };

  const handleStatusChange = async (record: THRRecord, status: string) => {
    try {
      await api.patch(`/api/v1/thr/${record.id}`, { status });
      fetchData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal mengubah status.');
    }
  };

  const getHolidayLabel = (value: string) =>
    HOLIDAY_OPTIONS.find((h) => h.value === value)?.label || value;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PAID':
        return 'bg-purple-100 text-purple-700';
      case 'APPROVED':
        return 'bg-emerald-100 text-emerald-700';
      default:
        return 'bg-yellow-100 text-yellow-700';
    }
  };

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">THR (Tunjangan Hari Raya)</h1>
          <p className="text-sm text-gray-500 mt-1">
            Kelola perhitungan THR berdasarkan hari raya keagamaan karyawan
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleCalculate}
            disabled={calculating}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {calculating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calculator className="w-4 h-4" />}
            Hitung Otomatis
          </button>
          <button
            onClick={openAddModal}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Tambah THR
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Tahun THR</label>
            <input
              type="number"
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Hari Raya</label>
            <select
              value={selectedHoliday}
              onChange={(e) => setSelectedHoliday(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              {HOLIDAY_OPTIONS.map((h) => (
                <option key={h.value} value={h.value}>{h.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
            <span className="ml-2 text-sm text-gray-500">Memuat data...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
            <p className="text-sm text-gray-600 mb-3">{error}</p>
            <button
              onClick={fetchData}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-emerald-600 border border-emerald-300 rounded-lg hover:bg-emerald-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Coba Lagi
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Karyawan</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Agama</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Hari Raya</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Masa Kerja (Bln)</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Jumlah THR</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Tanggal THR</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {records.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-12 text-gray-500">
                      Belum ada data THR. Klik &quot;Hitung Otomatis&quot; atau &quot;Tambah THR&quot;.
                    </td>
                  </tr>
                ) : (
                  records.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-900">{record.employee_name}</td>
                      <td className="py-3 px-4 text-gray-600">{record.employee_religion || '-'}</td>
                      <td className="py-3 px-4 text-gray-600">{getHolidayLabel(record.religious_holiday)}</td>
                      <td className="py-3 px-4 text-right">{record.tenure_months}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatIDR(Number(record.amount))}</td>
                      <td className="py-3 px-4 text-gray-600">{record.thr_date}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(record.status)}`}>
                          {record.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          {record.status === 'DRAFT' && (
                            <button
                              onClick={() => handleStatusChange(record, 'APPROVED')}
                              className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                              title="Approve"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => openEditModal(record)}
                            className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                            title="Edit"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeleteTarget(record)}
                            className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-red-600 transition-colors"
                            title="Hapus"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ─── Modal ───────────────────────────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowModal(false)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingRecord ? 'Edit' : 'Tambah'} THR
              </h3>
              <button onClick={() => setShowModal(false)} className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {!editingRecord && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Karyawan</label>
                  <select
                    value={formData.employee_id}
                    onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    <option value="">Pilih Karyawan</option>
                    {employees.map((emp) => (
                      <option key={emp.id} value={emp.id}>
                        {emp.first_name} {emp.last_name || ''} ({emp.employee_code})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tahun</label>
                  <input
                    type="number"
                    value={formData.thr_year}
                    onChange={(e) => setFormData({ ...formData, thr_year: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Hari Raya</label>
                  <select
                    value={formData.religious_holiday}
                    onChange={(e) => setFormData({ ...formData, religious_holiday: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    {HOLIDAY_OPTIONS.map((h) => (
                      <option key={h.value} value={h.value}>{h.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jumlah THR</label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="Contoh: 10000000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tanggal THR</label>
                <input
                  type="date"
                  value={formData.thr_date}
                  onChange={(e) => setFormData({ ...formData, thr_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Keterangan</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
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
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
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
              Hapus THR untuk <span className="font-semibold">{deleteTarget.employee_name}</span>?
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
