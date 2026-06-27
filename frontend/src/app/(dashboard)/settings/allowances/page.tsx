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
  List,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import AllowanceMatrixModal from '@/components/settings/AllowanceMatrixModal';

// ─── Types ───────────────────────────────────────────────────────────────────

interface AllowanceType {
  id: number;
  company_id: number;
  name: string;
  code: string;
  description: string | null;
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  amount_basis: 'UNIVERSAL' | 'GRADE' | 'POSITION' | 'DEPARTMENT' | 'INDIVIDUAL';
  is_taxable: boolean;
  is_bpjs_base: boolean;
  formula_template: string | null;
  sort_order: number;
  is_active: boolean;
}

interface FormData {
  name: string;
  code: string;
  description: string;
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  amount_basis: 'UNIVERSAL' | 'GRADE' | 'POSITION' | 'DEPARTMENT' | 'INDIVIDUAL';
  is_taxable: boolean;
  is_bpjs_base: boolean;
  formula_template: string;
  sort_order: string;
  is_active: boolean;
}

const EMPTY_FORM: FormData = {
  name: '',
  code: '',
  description: '',
  calculation_type: 'FIXED',
  amount_basis: 'UNIVERSAL',
  is_taxable: true,
  is_bpjs_base: true,
  formula_template: '',
  sort_order: '0',
  is_active: true,
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function AllowancesSettingsPage() {
  const [data, setData] = useState<AllowanceType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<AllowanceType | null>(null);
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<AllowanceType | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Matrix modal state
  const [matrixTarget, setMatrixTarget] = useState<AllowanceType | null>(null);

  // ─── Data Fetching ──────────────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<AllowanceType[]>('/api/v1/allowances/types?company_id=1');
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

  const openEditModal = (item: AllowanceType) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      code: item.code,
      description: item.description || '',
      calculation_type: item.calculation_type,
      amount_basis: item.amount_basis,
      is_taxable: item.is_taxable,
      is_bpjs_base: item.is_bpjs_base,
      formula_template: item.formula_template || '',
      sort_order: String(item.sort_order),
      is_active: item.is_active,
    });
    setFormError(null);
    setShowModal(true);
  };

  const buildBody = () => {
    return {
      company_id: 1,
      name: formData.name,
      code: formData.code,
      description: formData.description || null,
      calculation_type: formData.calculation_type,
      amount_basis: formData.amount_basis,
      is_taxable: formData.is_taxable,
      is_bpjs_base: formData.is_bpjs_base,
      formula_template: formData.calculation_type === 'FORMULA' ? formData.formula_template || null : null,
      sort_order: Number(formData.sort_order) || 0,
      is_active: formData.is_active,
    };
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);
    try {
      if (editingItem) {
        await api.patch(`/api/v1/allowances/types/${editingItem.id}`, buildBody());
      } else {
        await api.post('/api/v1/allowances/types', buildBody());
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
      await api.delete(`/api/v1/allowances/types/${deleteTarget.id}`);
      setDeleteTarget(null);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setDeleteError('Tidak dapat dihapus: tunjangan sedang digunakan oleh karyawan.');
      } else if (err instanceof ApiError) {
        setDeleteError(err.message);
      } else {
        setDeleteError('Terjadi kesalahan. Coba lagi.');
      }
    } finally {
      setDeleting(false);
    }
  };

  const getAmountBasisLabel = (basis: AllowanceType['amount_basis']) => {
    switch (basis) {
      case 'UNIVERSAL': return 'Sama untuk Semua';
      case 'GRADE': return 'Berdasarkan Grade';
      case 'POSITION': return 'Berdasarkan Jabatan';
      case 'DEPARTMENT': return 'Berdasarkan Departemen';
      case 'INDIVIDUAL': return 'Individu / Khusus';
      default: return basis;
    }
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
            className="border-b-2 border-emerald-500 text-emerald-600 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Tunjangan
          </Link>
          <Link
            href="/settings/bpjs"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
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
        <h1 className="text-2xl font-bold text-slate-800">Tunjangan</h1>
        <p className="text-sm text-slate-500 mt-1">
          Kelola jenis tunjangan perusahaan dan aturan perhitungannya
        </p>
      </div>

      {/* Content Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {/* Card Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-slate-800">Daftar Jenis Tunjangan</h2>
          <button
            onClick={openAddModal}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Tambah Tunjangan
          </button>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
              <span className="ml-2 text-sm text-slate-500">Memuat data...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
              <p className="text-sm text-slate-600 mb-3">{error}</p>
              <button
                onClick={fetchData}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-emerald-600 border border-emerald-300 rounded-lg hover:bg-emerald-50 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Coba Lagi
              </button>
            </div>
          ) : data.length === 0 ? (
            <div className="text-center py-12 text-sm text-slate-500">
              Belum ada data tunjangan. Klik &quot;Tambah Tunjangan&quot; untuk menambahkan.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Nama</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Kode</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Tipe</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Dasar Besaran</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Pajak</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">BPJS</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Urutan</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-slate-800 font-medium">{item.name}</td>
                    <td className="py-3 px-4 font-mono text-slate-700">{item.code}</td>
                    <td className="py-3 px-4 text-slate-600">{item.calculation_type}</td>
                    <td className="py-3 px-4 text-slate-600">{getAmountBasisLabel(item.amount_basis)}</td>
                    <td className="py-3 px-4 text-slate-600">{item.is_taxable ? 'Ya' : 'Tidak'}</td>
                    <td className="py-3 px-4 text-slate-600">{item.is_bpjs_base ? 'Ya' : 'Tidak'}</td>
                    <td className="py-3 px-4 text-slate-600">{item.sort_order}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${item.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                        {item.is_active ? 'Aktif' : 'Nonaktif'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        {(item.amount_basis === 'GRADE' || item.amount_basis === 'POSITION' || item.amount_basis === 'DEPARTMENT') && (
                          <button
                            onClick={() => setMatrixTarget(item)}
                            className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-blue-600 transition-colors"
                            title="Detail Nilai"
                          >
                            <List className="w-4 h-4" />
                          </button>
                        )}
                        <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors" title="Edit">
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
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-800">
                {editingItem ? 'Edit' : 'Tambah'} Tunjangan
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded-md hover:bg-gray-100 text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <FormField
                label="Nama Tunjangan"
                value={formData.name}
                onChange={(v) => setFormData({ ...formData, name: v })}
                placeholder="Contoh: Tunjangan Makan"
              />
              <FormField
                label="Kode"
                value={formData.code}
                onChange={(v) => setFormData({ ...formData, code: v })}
                placeholder="Contoh: MAKAN"
              />
              <FormField
                label="Deskripsi"
                value={formData.description}
                onChange={(v) => setFormData({ ...formData, description: v })}
                placeholder="Opsional"
              />

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Tipe Perhitungan</label>
                <select
                  value={formData.calculation_type}
                  onChange={(e) => setFormData({ ...formData, calculation_type: e.target.value as FormData['calculation_type'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="FIXED">FIXED - Nominal Tetap</option>
                  <option value="PERCENTAGE">PERCENTAGE - Persentase</option>
                  <option value="FORMULA">FORMULA - Rumus</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Dasar Besaran</label>
                <select
                  value={formData.amount_basis}
                  onChange={(e) => setFormData({ ...formData, amount_basis: e.target.value as FormData['amount_basis'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="UNIVERSAL">Sama untuk Semua Karyawan</option>
                  <option value="GRADE">Berdasarkan Grade</option>
                  <option value="POSITION">Berdasarkan Jabatan</option>
                  <option value="DEPARTMENT">Berdasarkan Departemen</option>
                  <option value="INDIVIDUAL">Individu / Khusus</option>
                </select>
              </div>

              {formData.calculation_type === 'FORMULA' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Template Rumus</label>
                  <textarea
                    value={formData.formula_template}
                    onChange={(e) => setFormData({ ...formData, formula_template: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="Contoh: {{basic_salary}} * 0.1"
                    rows={3}
                  />
                </div>
              )}

              <FormField
                label="Urutan"
                value={formData.sort_order}
                onChange={(v) => setFormData({ ...formData, sort_order: v })}
                type="number"
                placeholder="0"
              />

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={formData.is_taxable}
                    onChange={(e) => setFormData({ ...formData, is_taxable: e.target.checked })}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  Kena Pajak
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={formData.is_bpjs_base}
                    onChange={(e) => setFormData({ ...formData, is_bpjs_base: e.target.checked })}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  Dasar BPJS
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
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
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
              Apakah Anda yakin ingin menghapus <span className="font-semibold text-slate-800">{deleteTarget.name}</span>?
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

      {/* ─── Matrix Detail Modal ─────────────────────────────────────────────── */}
      {matrixTarget && (
        <AllowanceMatrixModal
          allowance={matrixTarget}
          onClose={() => setMatrixTarget(null)}
        />
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
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
        placeholder={placeholder}
      />
    </div>
  );
}
