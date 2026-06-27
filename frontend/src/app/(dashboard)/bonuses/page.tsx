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
  Award,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { formatIDR } from '@/lib/utils';
import { PaginatedResponse } from '@/types';

// ─── Types ───────────────────────────────────────────────────────────────────

interface BonusType {
  id: number;
  company_id: number;
  name: string;
  code: string;
  is_taxable: boolean;
  is_active: boolean;
}

interface Employee {
  id: number;
  first_name: string;
  last_name: string | null;
  employee_code: string;
}

interface Bonus {
  id: number;
  employee_id: number;
  employee_name: string;
  bonus_type_id: number;
  bonus_type_name: string;
  amount: string;
  bonus_date: string;
  description: string | null;
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  is_processed: boolean;
}

interface BonusTypeFormData {
  name: string;
  code: string;
  is_taxable: boolean;
  is_active: boolean;
}

interface BonusFormData {
  employee_id: string;
  bonus_type_id: string;
  amount: string;
  bonus_date: string;
  description: string;
}

const EMPTY_BONUS_TYPE_FORM: BonusTypeFormData = {
  name: '',
  code: '',
  is_taxable: true,
  is_active: true,
};

const EMPTY_BONUS_FORM: BonusFormData = {
  employee_id: '',
  bonus_type_id: '',
  amount: '',
  bonus_date: '',
  description: '',
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function BonusesPage() {
  const [activeTab, setActiveTab] = useState<'records' | 'types'>('records');

  const [bonusTypes, setBonusTypes] = useState<BonusType[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [bonuses, setBonuses] = useState<Bonus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [showTypeModal, setShowTypeModal] = useState(false);
  const [editingType, setEditingType] = useState<BonusType | null>(null);
  const [typeForm, setTypeForm] = useState<BonusTypeFormData>(EMPTY_BONUS_TYPE_FORM);
  const [typeFormError, setTypeFormError] = useState<string | null>(null);
  const [savingType, setSavingType] = useState(false);
  const [deleteTypeTarget, setDeleteTypeTarget] = useState<BonusType | null>(null);

  const [showBonusModal, setShowBonusModal] = useState(false);
  const [editingBonus, setEditingBonus] = useState<Bonus | null>(null);
  const [bonusForm, setBonusForm] = useState<BonusFormData>(EMPTY_BONUS_FORM);
  const [bonusFormError, setBonusFormError] = useState<string | null>(null);
  const [savingBonus, setSavingBonus] = useState(false);
  const [deleteBonusTarget, setDeleteBonusTarget] = useState<Bonus | null>(null);

  // ─── Data Fetching ──────────────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [typesData, empData, bonusData] = await Promise.all([
        api.get<BonusType[]>('/api/v1/bonuses/types?company_id=1'),
        api.get<PaginatedResponse<Employee>>('/api/v1/employees?company_id=1&skip=0&limit=1000'),
        api.get<Bonus[]>('/api/v1/bonuses?company_id=1'),
      ]);
      setBonusTypes(typesData);
      setEmployees(empData.items);
      setBonuses(bonusData);
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

  // ─── Bonus Type Handlers ────────────────────────────────────────────────────

  const openAddTypeModal = () => {
    setEditingType(null);
    setTypeForm(EMPTY_BONUS_TYPE_FORM);
    setTypeFormError(null);
    setShowTypeModal(true);
  };

  const openEditTypeModal = (item: BonusType) => {
    setEditingType(item);
    setTypeForm({
      name: item.name,
      code: item.code,
      is_taxable: item.is_taxable,
      is_active: item.is_active,
    });
    setTypeFormError(null);
    setShowTypeModal(true);
  };

  const handleSaveType = async () => {
    setSavingType(true);
    setTypeFormError(null);
    try {
      if (editingType) {
        await api.patch(`/api/v1/bonuses/types/${editingType.id}`, { ...typeForm, company_id: 1 });
      } else {
        await api.post('/api/v1/bonuses/types', { ...typeForm, company_id: 1 });
      }
      setShowTypeModal(false);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setTypeFormError(err.message);
      } else {
        setTypeFormError('Terjadi kesalahan. Coba lagi.');
      }
    } finally {
      setSavingType(false);
    }
  };

  const handleDeleteType = async () => {
    if (!deleteTypeTarget) return;
    try {
      await api.delete(`/api/v1/bonuses/types/${deleteTypeTarget.id}`);
      setDeleteTypeTarget(null);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    }
  };

  // ─── Bonus Record Handlers ──────────────────────────────────────────────────

  const openAddBonusModal = () => {
    setEditingBonus(null);
    setBonusForm({
      ...EMPTY_BONUS_FORM,
      bonus_date: new Date().toISOString().split('T')[0],
    });
    setBonusFormError(null);
    setShowBonusModal(true);
  };

  const openEditBonusModal = (item: Bonus) => {
    setEditingBonus(item);
    setBonusForm({
      employee_id: String(item.employee_id),
      bonus_type_id: String(item.bonus_type_id),
      amount: item.amount,
      bonus_date: item.bonus_date,
      description: item.description || '',
    });
    setBonusFormError(null);
    setShowBonusModal(true);
  };

  const handleSaveBonus = async () => {
    setSavingBonus(true);
    setBonusFormError(null);
    try {
      const body = {
        employee_id: Number(bonusForm.employee_id),
        bonus_type_id: Number(bonusForm.bonus_type_id),
        amount: Number(bonusForm.amount),
        bonus_date: bonusForm.bonus_date,
        description: bonusForm.description || null,
      };
      if (editingBonus) {
        await api.patch(`/api/v1/bonuses/${editingBonus.id}`, body);
      } else {
        await api.post('/api/v1/bonuses', body);
      }
      setShowBonusModal(false);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setBonusFormError(err.message);
      } else {
        setBonusFormError('Terjadi kesalahan. Coba lagi.');
      }
    } finally {
      setSavingBonus(false);
    }
  };

  const handleDeleteBonus = async () => {
    if (!deleteBonusTarget) return;
    try {
      await api.delete(`/api/v1/bonuses/${deleteBonusTarget.id}`);
      setDeleteBonusTarget(null);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    }
  };

  const handleApproveBonus = async (bonus: Bonus, status: 'APPROVED' | 'REJECTED') => {
    try {
      await api.patch(`/api/v1/bonuses/${bonus.id}`, { approval_status: status });
      fetchData();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal mengubah status approval.');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'bg-emerald-100 text-emerald-700';
      case 'REJECTED':
        return 'bg-red-100 text-red-700';
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
          <h1 className="text-2xl font-bold text-gray-900">Bonus</h1>
          <p className="text-sm text-gray-500 mt-1">
            Kelola jenis bonus dan pemberian bonus per karyawan
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('records')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'records'
                ? 'bg-emerald-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Data Bonus
          </button>
          <button
            onClick={() => setActiveTab('types')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'types'
                ? 'bg-emerald-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Jenis Bonus
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
          <span className="ml-2 text-sm text-gray-500">Memuat data...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12 bg-white rounded-xl border border-gray-200">
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
      ) : activeTab === 'records' ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">Daftar Bonus Karyawan</h2>
            <button
              onClick={openAddBonusModal}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Tambah Bonus
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Karyawan</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Jenis Bonus</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Jumlah</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Tanggal</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {bonuses.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-gray-500">
                      Belum ada data bonus.
                    </td>
                  </tr>
                ) : (
                  bonuses.map((bonus) => (
                    <tr key={bonus.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-900">{bonus.employee_name}</td>
                      <td className="py-3 px-4 text-gray-600">{bonus.bonus_type_name}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatIDR(Number(bonus.amount))}</td>
                      <td className="py-3 px-4 text-gray-600">{bonus.bonus_date}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(bonus.approval_status)}`}>
                          {bonus.approval_status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          {bonus.approval_status === 'PENDING' && !bonus.is_processed && (
                            <>
                              <button
                                onClick={() => handleApproveBonus(bonus, 'APPROVED')}
                                className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                                title="Approve"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleApproveBonus(bonus, 'REJECTED')}
                                className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-red-600 transition-colors"
                                title="Reject"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => openEditBonusModal(bonus)}
                            className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                            title="Edit"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeleteBonusTarget(bonus)}
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
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">Jenis Bonus</h2>
            <button
              onClick={openAddTypeModal}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Tambah Jenis
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Nama</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Kode</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Kena Pajak</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {bonusTypes.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-12 text-gray-500">
                      Belum ada jenis bonus.
                    </td>
                  </tr>
                ) : (
                  bonusTypes.map((type) => (
                    <tr key={type.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-900 font-medium">{type.name}</td>
                      <td className="py-3 px-4 font-mono text-gray-700">{type.code}</td>
                      <td className="py-3 px-4 text-gray-600">{type.is_taxable ? 'Ya' : 'Tidak'}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${type.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                          {type.is_active ? 'Aktif' : 'Nonaktif'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => openEditTypeModal(type)}
                            className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                            title="Edit"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeleteTypeTarget(type)}
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
        </div>
      )}

      {/* ─── Bonus Modal ─────────────────────────────────────────────────────── */}
      {showBonusModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowBonusModal(false)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingBonus ? 'Edit' : 'Tambah'} Bonus
              </h3>
              <button onClick={() => setShowBonusModal(false)} className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Karyawan</label>
                <select
                  value={bonusForm.employee_id}
                  onChange={(e) => setBonusForm({ ...bonusForm, employee_id: e.target.value })}
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

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jenis Bonus</label>
                <select
                  value={bonusForm.bonus_type_id}
                  onChange={(e) => setBonusForm({ ...bonusForm, bonus_type_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Pilih Jenis Bonus</option>
                  {bonusTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jumlah</label>
                <input
                  type="number"
                  value={bonusForm.amount}
                  onChange={(e) => setBonusForm({ ...bonusForm, amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="Contoh: 5000000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tanggal Bonus</label>
                <input
                  type="date"
                  value={bonusForm.bonus_date}
                  onChange={(e) => setBonusForm({ ...bonusForm, bonus_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Keterangan</label>
                <textarea
                  value={bonusForm.description}
                  onChange={(e) => setBonusForm({ ...bonusForm, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>
            </div>

            {bonusFormError && (
              <div className="mt-3 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {bonusFormError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setShowBonusModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleSaveBonus}
                disabled={savingBonus}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {savingBonus && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Bonus Type Modal ────────────────────────────────────────────────── */}
      {showTypeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowTypeModal(false)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingType ? 'Edit' : 'Tambah'} Jenis Bonus
              </h3>
              <button onClick={() => setShowTypeModal(false)} className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nama</label>
                <input
                  type="text"
                  value={typeForm.name}
                  onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="Contoh: Bonus Kinerja"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Kode</label>
                <input
                  type="text"
                  value={typeForm.code}
                  onChange={(e) => setTypeForm({ ...typeForm, code: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="Contoh: BNS-KINERJA"
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={typeForm.is_taxable}
                    onChange={(e) => setTypeForm({ ...typeForm, is_taxable: e.target.checked })}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  Kena Pajak
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={typeForm.is_active}
                    onChange={(e) => setTypeForm({ ...typeForm, is_active: e.target.checked })}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  Aktif
                </label>
              </div>
            </div>

            {typeFormError && (
              <div className="mt-3 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {typeFormError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setShowTypeModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleSaveType}
                disabled={savingType}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {savingType && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Delete Confirmation ─────────────────────────────────────────────── */}
      {(deleteBonusTarget || deleteTypeTarget) && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/30" onClick={() => { setDeleteBonusTarget(null); setDeleteTypeTarget(null); }} />
          <div className="relative bg-white rounded-xl shadow-xl border border-red-100 p-6 w-full max-w-sm mx-4">
            <h4 className="text-base font-semibold text-gray-900 mb-2">Konfirmasi Hapus</h4>
            <p className="text-sm text-gray-600 mb-4">
              Hapus <span className="font-semibold">{deleteBonusTarget?.employee_name || deleteTypeTarget?.name}</span>?
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => { setDeleteBonusTarget(null); setDeleteTypeTarget(null); }}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={() => {
                  if (deleteBonusTarget) handleDeleteBonus();
                  if (deleteTypeTarget) handleDeleteType();
                }}
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
