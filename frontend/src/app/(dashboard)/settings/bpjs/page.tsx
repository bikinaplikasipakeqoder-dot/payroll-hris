'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Plus,
  Pencil,
  Trash2,
  X,
  Loader2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';

// ─── Types ───────────────────────────────────────────────────────────────────

type BpjsType = 'KESEHATAN' | 'JHT' | 'JP' | 'JKK' | 'JKM';

const BPJS_TYPES: { value: BpjsType; label: string }[] = [
  { value: 'KESEHATAN', label: 'Kesehatan' },
  { value: 'JHT', label: 'Jaminan Hari Tua (JHT)' },
  { value: 'JP', label: 'Jaminan Pensiun (JP)' },
  { value: 'JKK', label: 'Jaminan Kecelakaan Kerja (JKK)' },
  { value: 'JKM', label: 'Jaminan Kematian (JKM)' },
];

interface BpjsSetting {
  id: number;
  company_id: number;
  bpjs_type: BpjsType;
  employee_rate: string;
  employer_rate: string;
  max_salary_base: string | null;
  regulation_year: number;
  effective_date: string;
  end_date: string | null;
  is_active: boolean;
}

interface FormData {
  bpjs_type: BpjsType;
  employee_rate: string;
  employer_rate: string;
  max_salary_base: string;
  regulation_year: string;
  effective_date: string;
  end_date: string;
  is_active: boolean;
}

const EMPTY_FORM: FormData = {
  bpjs_type: 'KESEHATAN',
  employee_rate: '',
  employer_rate: '',
  max_salary_base: '',
  regulation_year: String(new Date().getFullYear()),
  effective_date: new Date().toISOString().split('T')[0],
  end_date: '',
  is_active: true,
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function BpjsSettingsPage() {
  const [data, setData] = useState<BpjsSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<BpjsSetting | null>(null);
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<BpjsSetting | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // ─── Data Fetching ──────────────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<BpjsSetting[]>('/api/v1/bpjs/settings?company_id=1');
      setData(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Gagal memuat data: ${err.message}`);
      } else {
        setError('Tidak dapat terhubung ke server. Pastikan backend sedang berjalan.');
      }
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ─── CRUD Handlers ──────────────────────────────────────────────────────────

  const openAddModal = () => {
    setEditingItem(null);
    setFormData(EMPTY_FORM);
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (item: BpjsSetting) => {
    setEditingItem(item);
    setFormData({
      bpjs_type: item.bpjs_type,
      employee_rate: item.employee_rate,
      employer_rate: item.employer_rate,
      max_salary_base: item.max_salary_base || '',
      regulation_year: String(item.regulation_year),
      effective_date: item.effective_date,
      end_date: item.end_date || '',
      is_active: item.is_active,
    });
    setFormError(null);
    setShowModal(true);
  };

  const buildBody = () => {
    return {
      company_id: 1,
      bpjs_type: formData.bpjs_type,
      employee_rate: formData.employee_rate,
      employer_rate: formData.employer_rate,
      max_salary_base: formData.max_salary_base ? Number(formData.max_salary_base) : null,
      regulation_year: Number(formData.regulation_year),
      effective_date: formData.effective_date,
      end_date: formData.end_date || null,
      is_active: formData.is_active,
    };
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);
    try {
      if (editingItem) {
        await api.patch(`/api/v1/bpjs/settings/${editingItem.id}`, buildBody());
      } else {
        await api.post('/api/v1/bpjs/settings', buildBody());
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
    setDeleting(true);
    setDeleteError(null);
    try {
      await api.delete(`/api/v1/bpjs/settings/${deleteTarget.id}`);
      setDeleteTarget(null);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setDeleteError(err.message);
      } else {
        setDeleteError('Terjadi kesalahan. Coba lagi.');
      }
    } finally {
      setDeleting(false);
    }
  };

  const getBpjsLabel = (type: BpjsType) => {
    return BPJS_TYPES.find((t) => t.value === type)?.label || type;
  };

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div>
      {/* Settings Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <Link
            href="/settings/ai"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Pengaturan AI
          </Link>
          <Link
            href="/settings/users"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Manajemen Pengguna
          </Link>
          <Link
            href="/settings/master-data"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Master Data
          </Link>
          <Link
            href="/settings/allowances"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Tunjangan
          </Link>
          <Link
            href="/settings/bpjs"
            className="border-b-2 border-rose-500 text-rose-600 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            BPJS
          </Link>
          <Link
            href="/settings/iuran"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Iuran
          </Link>
          <Link
            href="/settings/tax"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            PPh 21
          </Link>
        </nav>
      </div>

      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">BPJS</h1>
        <p className="text-sm text-slate-500 mt-1">
          Atur tarif iuran BPJS Kesehatan, JHT, JP, JKK, dan JKM
        </p>
      </div>

      {/* Content Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {/* Card Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-slate-800">Daftar Pengaturan BPJS</h2>
          <button
            onClick={openAddModal}
            className="inline-flex items-center gap-2 px-4 py-2 bg-rose-600 text-white text-sm font-medium rounded-lg hover:bg-rose-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Tambah Pengaturan BPJS
          </button>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-rose-600" />
              <span className="ml-2 text-sm text-slate-500">Memuat data...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
              <p className="text-sm text-slate-600 mb-3">{error}</p>
              <button
                onClick={fetchData}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-rose-600 border border-rose-300 rounded-lg hover:bg-rose-50 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Coba Lagi
              </button>
            </div>
          ) : data.length === 0 ? (
            <div className="text-center py-12 text-sm text-slate-500">
              Belum ada pengaturan BPJS. Klik &quot;Tambah Pengaturan BPJS&quot; untuk menambahkan.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Jenis BPJS</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Karyawan (%)</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Perusahaan (%)</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Maksimal Dasar Gaji</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Tahun Regulasi</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Efektif</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Berakhir</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-slate-800 font-medium">{getBpjsLabel(item.bpjs_type)}</td>
                    <td className="py-3 px-4 text-slate-600">{item.employee_rate}</td>
                    <td className="py-3 px-4 text-slate-600">{item.employer_rate}</td>
                    <td className="py-3 px-4 text-slate-600">{item.max_salary_base ? Number(item.max_salary_base).toLocaleString('id-ID') : '-'}</td>
                    <td className="py-3 px-4 text-slate-600">{item.regulation_year}</td>
                    <td className="py-3 px-4 text-slate-600">{item.effective_date}</td>
                    <td className="py-3 px-4 text-slate-600">{item.end_date || '-'}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${item.is_active ? 'bg-rose-100 text-rose-700' : 'bg-gray-100 text-gray-600'}`}>
                        {item.is_active ? 'Aktif' : 'Nonaktif'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-rose-50 text-slate-500 hover:text-rose-600 transition-colors" title="Edit">
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button onClick={() => { setDeleteTarget(item); setDeleteError(null); }} className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-red-600 transition-colors" title="Hapus">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* ─── Add/Edit Modal ──────────────────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-lg mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-800">
                {editingItem ? 'Edit' : 'Tambah'} Pengaturan BPJS
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded-md hover:bg-gray-100 text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Jenis BPJS</label>
                <select
                  value={formData.bpjs_type}
                  onChange={(e) => setFormData({ ...formData, bpjs_type: e.target.value as BpjsType })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-rose-500"
                >
                  {BPJS_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="Tarif Karyawan (%)"
                  value={formData.employee_rate}
                  onChange={(v) => setFormData({ ...formData, employee_rate: v })}
                  placeholder="Contoh: 0.01"
                />
                <FormField
                  label="Tarif Perusahaan (%)"
                  value={formData.employer_rate}
                  onChange={(v) => setFormData({ ...formData, employer_rate: v })}
                  placeholder="Contoh: 0.04"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="Maksimal Dasar Gaji (opsional)"
                  value={formData.max_salary_base}
                  onChange={(v) => setFormData({ ...formData, max_salary_base: v })}
                  placeholder="Contoh: 12000000"
                />
                <FormField
                  label="Tahun Regulasi"
                  value={formData.regulation_year}
                  onChange={(v) => setFormData({ ...formData, regulation_year: v })}
                  placeholder="Contoh: 2024"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="Tanggal Efektif"
                  value={formData.effective_date}
                  onChange={(v) => setFormData({ ...formData, effective_date: v })}
                  type="date"
                />
                <FormField
                  label="Tanggal Berakhir (opsional)"
                  value={formData.end_date}
                  onChange={(v) => setFormData({ ...formData, end_date: v })}
                  type="date"
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-rose-600 border-gray-300 rounded focus:ring-rose-500"
                  />
                  Aktif
                </label>
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
                className="px-4 py-2 text-sm font-medium text-slate-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-rose-600 rounded-lg hover:bg-rose-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Delete Confirmation Modal ───────────────────────────────────────── */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setDeleteTarget(null)}
          />
          <div className="relative bg-white rounded-xl shadow-xl border border-red-100 p-6 w-full max-w-sm mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-800">Konfirmasi Hapus</h3>
              <button
                onClick={() => setDeleteTarget(null)}
                className="p-1 rounded-md hover:bg-gray-100 text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-sm text-slate-600 mb-4">
              Apakah Anda yakin ingin menghapus pengaturan <span className="font-semibold text-slate-800">{getBpjsLabel(deleteTarget.bpjs_type)}</span>?
            </p>

            {deleteError && (
              <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {deleteError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 text-sm font-medium text-slate-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting && <Loader2 className="w-4 h-4 animate-spin" />}
                Ya, Hapus
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Reusable Form Field ──────────────────────────────────────────────────────

function FormField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-rose-500"
        placeholder={placeholder}
      />
    </div>
  );
}
