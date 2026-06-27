'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Plus, Pencil, Trash2, X, Loader2 } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { UmpSetting } from '@/types';

interface FormData {
  province: string;
  city: string;
  amount: string;
  effective_date: string;
}

const EMPTY_FORM: FormData = {
  province: '',
  city: '',
  amount: '',
  effective_date: new Date().toISOString().split('T')[0],
};

export default function UmpSettingsPage() {
  const [data, setData] = useState<UmpSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<UmpSetting | null>(null);
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<UmpSetting[]>('/api/v1/companies/1/ump-settings');
      setData(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Gagal memuat data UMP');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const openAddModal = () => {
    setEditingItem(null);
    setFormData(EMPTY_FORM);
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (item: UmpSetting) => {
    setEditingItem(item);
    setFormData({
      province: item.province,
      city: item.city || '',
      amount: String(item.amount),
      effective_date: item.effective_date,
    });
    setFormError(null);
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);
    try {
      const body = {
        company_id: 1,
        province: formData.province,
        city: formData.city || null,
        amount: Number(formData.amount),
        effective_date: formData.effective_date,
      };
      if (editingItem) {
        await api.patch(`/api/v1/companies/1/ump-settings/${editingItem.id}`, body);
      } else {
        await api.post('/api/v1/companies/1/ump-settings', body);
      }
      setShowModal(false);
      fetchData();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Terjadi kesalahan saat menyimpan');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (item: UmpSetting) => {
    if (!confirm(`Hapus UMP ${item.province}${item.city ? ` - ${item.city}` : ''}?`)) return;
    try {
      await api.delete(`/api/v1/companies/1/ump-settings/${item.id}`);
      fetchData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menghapus UMP');
    }
  };

  const formatMoney = (value: number) =>
    new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value);

  return (
    <div>
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {['ai', 'users', 'master-data', 'allowances', 'bpjs', 'tax', 'iuran', 'entities', 'ump'].map((tab) => (
            <Link
              key={tab}
              href={`/settings/${tab}`}
              className={`border-b-2 whitespace-nowrap py-3 px-1 text-sm font-medium ${
                tab === 'ump'
                  ? 'border-teal-500 text-teal-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab === 'ai' && 'AI'}
              {tab === 'master-data' && 'Master Data'}
              {tab === 'allowances' && 'Tunjangan'}
              {tab === 'bpjs' && 'BPJS'}
              {tab === 'tax' && 'PPh 21'}
              {tab === 'iuran' && 'Iuran'}
              {tab === 'entities' && 'Entitas'}
              {tab === 'ump' && 'UMP'}
              {tab === 'users' && 'Pengguna'}
            </Link>
          ))}
        </nav>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">UMP Regional</h1>
          <p className="text-sm text-slate-500 mt-1">Atur Upah Minimum Provinsi/Kota</p>
        </div>
        <button
          onClick={openAddModal}
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 text-sm font-medium"
        >
          <Plus className="w-4 h-4" /> Tambah UMP
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
        </div>
      ) : data.length === 0 ? (
        <div className="text-center py-12 text-gray-500 bg-white rounded-xl border border-gray-200">
          Belum ada data UMP
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provinsi</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kota</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nominal</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Berlaku Sejak</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">{item.province}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.city || '-'}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{formatMoney(item.amount)}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{item.effective_date}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => openEditModal(item)} className="p-1 text-amber-600 hover:bg-amber-50 rounded">
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(item)} className="p-1 text-red-600 hover:bg-red-50 rounded">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold">{editingItem ? 'Edit UMP' : 'Tambah UMP'}</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              {formError && <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-sm">{formError}</div>}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Provinsi *</label>
                <input
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={formData.province}
                  onChange={(e) => setFormData({ ...formData, province: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Kota (opsional)</label>
                <input
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nominal UMP *</label>
                <input
                  type="number"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Berlaku Sejak *</label>
                <input
                  type="date"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={formData.effective_date}
                  onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t border-gray-200">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg">
                Batal
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !formData.province || !formData.amount || !formData.effective_date}
                className="px-4 py-2 text-sm font-medium bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Simpan'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
