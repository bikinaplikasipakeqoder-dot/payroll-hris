'use client';

import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, X, Loader2, AlertCircle } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { EmployeeAllowance } from '@/types';

interface AllowanceType {
  id: number;
  name: string;
  code: string;
}

interface EmployeeAllowancesProps {
  employeeId: number;
}

interface FormData {
  allowance_type_id: string;
  amount: string;
  effective_date: string;
  end_date: string;
  notes: string;
  is_active: boolean;
}

export default function EmployeeAllowances({ employeeId }: EmployeeAllowancesProps) {
  const [allowances, setAllowances] = useState<EmployeeAllowance[]>([]);
  const [allowanceTypes, setAllowanceTypes] = useState<AllowanceType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<EmployeeAllowance | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [formData, setFormData] = useState<FormData>({
    allowance_type_id: '',
    amount: '',
    effective_date: new Date().toISOString().split('T')[0],
    end_date: '',
    notes: '',
    is_active: true,
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [allowanceData, typeData] = await Promise.all([
        api.get<EmployeeAllowance[]>(`/api/v1/employees/${employeeId}/allowances`),
        api.get<AllowanceType[]>('/api/v1/allowances/types?company_id=1'),
      ]);
      setAllowances(allowanceData);
      setAllowanceTypes(typeData);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Gagal memuat data tunjangan.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [employeeId]);

  const resetForm = () => {
    setFormData({
      allowance_type_id: '',
      amount: '',
      effective_date: new Date().toISOString().split('T')[0],
      end_date: '',
      notes: '',
      is_active: true,
    });
  };

  const openAdd = () => {
    setEditingItem(null);
    resetForm();
    setFormError(null);
    setShowModal(true);
  };

  const openEdit = (item: EmployeeAllowance) => {
    setEditingItem(item);
    setFormData({
      allowance_type_id: String(item.allowance_type_id),
      amount: String(item.amount),
      effective_date: item.effective_date,
      end_date: item.end_date || '',
      notes: item.notes || '',
      is_active: item.is_active,
    });
    setFormError(null);
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);

    const body = {
      allowance_type_id: Number(formData.allowance_type_id),
      amount: Number(formData.amount),
      effective_date: formData.effective_date,
      end_date: formData.end_date || null,
      notes: formData.notes || null,
      is_active: formData.is_active,
    };

    try {
      if (editingItem) {
        await api.patch(`/api/v1/employees/${employeeId}/allowances/${editingItem.id}`, body);
      } else {
        await api.post(`/api/v1/employees/${employeeId}/allowances`, body);
      }
      setShowModal(false);
      resetForm();
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(err.message);
      } else {
        setFormError('Gagal menyimpan tunjangan.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Apakah Anda yakin ingin menghapus tunjangan ini?')) return;
    setDeletingId(id);
    try {
      await api.delete(`/api/v1/employees/${employeeId}/allowances/${id}`);
      fetchData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menghapus tunjangan.');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
        <span className="ml-2 text-sm text-gray-500">Memuat tunjangan...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
        <p className="text-sm text-gray-600 mb-3">{error}</p>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 border border-primary-300 rounded-lg hover:bg-primary-50 transition-colors"
        >
          Coba Lagi
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-900">Tunjangan Karyawan</h3>
        <button
          onClick={openAdd}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Tambah Tunjangan
        </button>
      </div>

      {allowances.length === 0 ? (
        <div className="text-center py-12 text-sm text-gray-500 bg-gray-50 rounded-lg border border-dashed border-gray-300">
          Belum ada tunjangan untuk karyawan ini.
        </div>
      ) : (
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left py-3 px-4 font-medium text-gray-600">Jenis Tunjangan</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Jumlah</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600">Efektif</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600">Berakhir</th>
                <th className="text-center py-3 px-4 font-medium text-gray-600">Status</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {allowances.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4 text-gray-900 font-medium">{item.allowance_type_name}</td>
                  <td className="py-3 px-4 text-right text-gray-700">{Number(item.amount).toLocaleString('id-ID')}</td>
                  <td className="py-3 px-4 text-gray-600">{item.effective_date}</td>
                  <td className="py-3 px-4 text-gray-600">{item.end_date || '-'}</td>
                  <td className="py-3 px-4 text-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${item.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {item.is_active ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => openEdit(item)}
                        className="p-1.5 rounded-md hover:bg-primary-50 text-gray-500 hover:text-primary-600 transition-colors"
                        title="Edit"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        disabled={deletingId === item.id}
                        className="p-1.5 rounded-md hover:bg-red-50 text-gray-500 hover:text-red-600 transition-colors disabled:opacity-50"
                        title="Hapus"
                      >
                        {deletingId === item.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowModal(false)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingItem ? 'Edit Tunjangan' : 'Tambah Tunjangan'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jenis Tunjangan</label>
                <select
                  value={formData.allowance_type_id}
                  onChange={(e) => setFormData({ ...formData, allowance_type_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Pilih jenis tunjangan</option>
                  {allowanceTypes.map((type) => (
                    <option key={type.id} value={type.id}>{type.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jumlah</label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="0"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tanggal Efektif</label>
                  <input
                    type="date"
                    value={formData.effective_date}
                    onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tanggal Berakhir (opsional)</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Catatan (opsional)</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">Aktif</label>
              </div>
            </div>

            {formError && (
              <div className="mt-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
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
                disabled={saving || !formData.allowance_type_id || !formData.amount || !formData.effective_date}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
