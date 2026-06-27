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
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface AllowanceType {
  id: number;
  company_id: number;
  name: string;
  code: string;
  calculation_type: 'FIXED' | 'PERCENTAGE' | 'FORMULA';
  amount_basis: 'UNIVERSAL' | 'GRADE' | 'POSITION' | 'DEPARTMENT' | 'INDIVIDUAL';
}

interface MatrixRow {
  id: number;
  allowance_type_id: number;
  entity_id: number;
  entity_name: string;
  amount: string;
  effective_date: string;
  end_date: string | null;
  is_active: boolean;
}

interface MasterEntity {
  id: number;
  name: string;
}

interface FormData {
  entity_id: string;
  amount: string;
  effective_date: string;
  end_date: string;
  is_active: boolean;
}

const EMPTY_FORM: FormData = {
  entity_id: '',
  amount: '',
  effective_date: '',
  end_date: '',
  is_active: true,
};

const BASIS_LABELS: Record<string, string> = {
  GRADE: 'Grade',
  POSITION: 'Jabatan',
  DEPARTMENT: 'Departemen',
};

const MASTER_ENDPOINTS: Record<string, string> = {
  GRADE: '/api/v1/master-data/grades',
  POSITION: '/api/v1/master-data/positions',
  DEPARTMENT: '/api/v1/master-data/departments',
};

// ─── Component ───────────────────────────────────────────────────────────────

interface AllowanceMatrixModalProps {
  allowance: AllowanceType;
  onClose: () => void;
}

export default function AllowanceMatrixModal({ allowance, onClose }: AllowanceMatrixModalProps) {
  const basis = allowance.amount_basis as 'GRADE' | 'POSITION' | 'DEPARTMENT';
  if (!['GRADE', 'POSITION', 'DEPARTMENT'].includes(basis)) {
    return null;
  }
  const [rows, setRows] = useState<MatrixRow[]>([]);
  const [entities, setEntities] = useState<MasterEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editingRow, setEditingRow] = useState<MatrixRow | null>(null);
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<MatrixRow | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchRows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [matrixData, entityData] = await Promise.all([
        api.get<MatrixRow[]>(
          `/api/v1/allowances/types/${allowance.id}/matrix?basis=${basis}`
        ),
        api.get<MasterEntity[]>(`${MASTER_ENDPOINTS[basis]}?company_id=${allowance.company_id}`),
      ]);
      setRows(matrixData);
      setEntities(entityData);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Gagal memuat data: ${err.message}`);
      } else {
        setError('Tidak dapat terhubung ke server.');
      }
    } finally {
      setLoading(false);
    }
  }, [allowance, basis]);

  useEffect(() => {
    fetchRows();
  }, [fetchRows]);

  const openAddForm = () => {
    setEditingRow(null);
    setFormData({
      ...EMPTY_FORM,
      effective_date: new Date().toISOString().split('T')[0],
    });
    setFormError(null);
    setShowForm(true);
  };

  const openEditForm = (row: MatrixRow) => {
    setEditingRow(row);
    setFormData({
      entity_id: String(row.entity_id),
      amount: row.amount,
      effective_date: row.effective_date,
      end_date: row.end_date || '',
      is_active: row.is_active,
    });
    setFormError(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);

    const body = {
      entity_id: Number(formData.entity_id),
      amount: Number(formData.amount),
      effective_date: formData.effective_date,
      end_date: formData.end_date || null,
      is_active: formData.is_active,
    };

    try {
      if (editingRow) {
        await api.patch(
          `/api/v1/allowances/matrix/${editingRow.id}?basis=${basis}`,
          body
        );
      } else {
        await api.post(
          `/api/v1/allowances/types/${allowance.id}/matrix?basis=${basis}`,
          body
        );
      }
      setShowForm(false);
      fetchRows();
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
    try {
      await api.delete(`/api/v1/allowances/matrix/${deleteTarget.id}?basis=${basis}`);
      setDeleteTarget(null);
      fetchRows();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    } finally {
      setDeleting(false);
    }
  };

  const formatIdr = (value: string | number) => {
    const num = Number(value);
    if (Number.isNaN(num)) return '-';
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(num);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-800">
              Detail Tunjangan per {BASIS_LABELS[basis]}
            </h3>
            <p className="text-sm text-slate-500">
              {allowance.name} ({allowance.code})
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-gray-100 text-slate-400 hover:text-slate-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-slate-600">
            Tentukan besaran tunjangan untuk setiap {BASIS_LABELS[basis].toLowerCase()}.
          </p>
          <button
            onClick={openAddForm}
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Tambah
          </button>
        </div>

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
              onClick={fetchRows}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-emerald-600 border border-emerald-300 rounded-lg hover:bg-emerald-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Coba Lagi
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-2 px-3 font-medium text-slate-600">
                    {BASIS_LABELS[basis]}
                  </th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Besaran</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Mulai</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Berakhir</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Status</th>
                  <th className="text-right py-2 px-3 font-medium text-slate-600">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-slate-500">
                      Belum ada data. Klik &quot;Tambah&quot; untuk menambahkan.
                    </td>
                  </tr>
                ) : (
                  rows.map((row) => (
                    <tr key={row.id} className="hover:bg-gray-50">
                      <td className="py-2 px-3 text-slate-800">{row.entity_name}</td>
                      <td className="py-2 px-3 text-slate-700">
                        {formatIdr(row.amount)}
                      </td>
                      <td className="py-2 px-3 text-slate-600">{row.effective_date}</td>
                      <td className="py-2 px-3 text-slate-600">{row.end_date || '-'}</td>
                      <td className="py-2 px-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            row.is_active
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {row.is_active ? 'Aktif' : 'Nonaktif'}
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => openEditForm(row)}
                            className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                            title="Edit"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeleteTarget(row)}
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

        {/* ─── Add/Edit Form ─────────────────────────────────────────────────── */}
        {showForm && (
          <div className="mt-6 border-t border-gray-200 pt-6">
            <h4 className="text-base font-semibold text-slate-800 mb-4">
              {editingRow ? 'Edit' : 'Tambah'} Detail
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  {BASIS_LABELS[basis]}
                </label>
                <select
                  value={formData.entity_id}
                  onChange={(e) => setFormData({ ...formData, entity_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Pilih {BASIS_LABELS[basis]}</option>
                  {entities.map((entity) => (
                    <option key={entity.id} value={entity.id}>
                      {entity.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Besaran</label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="Contoh: 1000000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Tanggal Efektif
                </label>
                <input
                  type="date"
                  value={formData.effective_date}
                  onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Tanggal Berakhir <span className="text-slate-400">(Opsional)</span>
                </label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center gap-2 md:col-span-2">
                <input
                  type="checkbox"
                  id="matrix-active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                />
                <label htmlFor="matrix-active" className="text-sm text-slate-700">
                  Aktif
                </label>
              </div>
            </div>

            {formError && (
              <div className="mt-3 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {formError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 mt-4">
              <button
                onClick={() => setShowForm(false)}
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
        )}

        {/* ─── Delete Confirmation ───────────────────────────────────────────── */}
        {deleteTarget && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center">
            <div className="absolute inset-0 bg-black/30" onClick={() => setDeleteTarget(null)} />
            <div className="relative bg-white rounded-xl shadow-xl border border-red-100 p-6 w-full max-w-sm mx-4">
              <h4 className="text-base font-semibold text-slate-800 mb-2">Konfirmasi Hapus</h4>
              <p className="text-sm text-slate-600 mb-4">
                Hapus detail untuk <span className="font-semibold">{deleteTarget.entity_name}</span>?
              </p>
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
                  Hapus
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
