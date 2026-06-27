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
  Receipt,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { formatIDR } from '@/lib/utils';
import { PaginatedResponse } from '@/types';
import { EmployeeSearchSelect } from '@/components/employees/EmployeeSearchSelect';
import { ExcelActions } from '@/components/ui/ExcelActions';

// ─── Types ───────────────────────────────────────────────────────────────────

interface ReimbursementType {
  id: number;
  company_id: number;
  name: string;
  code: string;
  max_amount: string | null;
  is_taxable: boolean;
  is_active: boolean;
}

interface Employee {
  id: number;
  first_name: string;
  last_name: string | null;
  employee_code: string;
}

interface Reimbursement {
  id: number;
  employee_id: number;
  employee_name: string;
  reimbursement_type_id: number;
  reimbursement_type_name: string;
  claim_amount: string;
  approved_amount: string | null;
  claim_date: string;
  expense_date: string;
  description: string | null;
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  is_processed: boolean;
}

interface ReimbursementTypeFormData {
  name: string;
  code: string;
  max_amount: string;
  is_taxable: boolean;
  is_active: boolean;
}

interface ReimbursementFormData {
  employee_id: string;
  reimbursement_type_id: string;
  claim_amount: string;
  claim_date: string;
  expense_date: string;
  description: string;
  receipt_path: string;
}

const EMPTY_TYPE_FORM: ReimbursementTypeFormData = {
  name: '',
  code: '',
  max_amount: '',
  is_taxable: true,
  is_active: true,
};

const EMPTY_REIMBURSEMENT_FORM: ReimbursementFormData = {
  employee_id: '',
  reimbursement_type_id: '',
  claim_amount: '',
  claim_date: '',
  expense_date: '',
  description: '',
  receipt_path: '',
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function ReimbursementsPage() {
  const [activeTab, setActiveTab] = useState<'records' | 'types'>('records');

  const [reimbursementTypes, setReimbursementTypes] = useState<ReimbursementType[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [reimbursements, setReimbursements] = useState<Reimbursement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [showTypeModal, setShowTypeModal] = useState(false);
  const [editingType, setEditingType] = useState<ReimbursementType | null>(null);
  const [typeForm, setTypeForm] = useState<ReimbursementTypeFormData>(EMPTY_TYPE_FORM);
  const [typeFormError, setTypeFormError] = useState<string | null>(null);
  const [savingType, setSavingType] = useState(false);
  const [deleteTypeTarget, setDeleteTypeTarget] = useState<ReimbursementType | null>(null);

  const [showReimbursementModal, setShowReimbursementModal] = useState(false);
  const [editingReimbursement, setEditingReimbursement] = useState<Reimbursement | null>(null);
  const [reimbursementForm, setReimbursementForm] = useState<ReimbursementFormData>(EMPTY_REIMBURSEMENT_FORM);
  const [reimbursementFormError, setReimbursementFormError] = useState<string | null>(null);
  const [savingReimbursement, setSavingReimbursement] = useState(false);
  const [deleteReimbursementTarget, setDeleteReimbursementTarget] = useState<Reimbursement | null>(null);

  // ─── Data Fetching ──────────────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [typesData, empData, reimbursementData] = await Promise.all([
        api.get<ReimbursementType[]>('/api/v1/reimbursements/types?company_id=1'),
        api.get<PaginatedResponse<Employee>>('/api/v1/employees?company_id=1&skip=0&limit=1000'),
        api.get<Reimbursement[]>('/api/v1/reimbursements?company_id=1'),
      ]);
      setReimbursementTypes(typesData);
      setEmployees(empData.items);
      setReimbursements(reimbursementData);
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

  // ─── Reimbursement Type Handlers ────────────────────────────────────────────

  const openAddTypeModal = () => {
    setEditingType(null);
    setTypeForm(EMPTY_TYPE_FORM);
    setTypeFormError(null);
    setShowTypeModal(true);
  };

  const openEditTypeModal = (item: ReimbursementType) => {
    setEditingType(item);
    setTypeForm({
      name: item.name,
      code: item.code,
      max_amount: item.max_amount || '',
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
      const body = {
        ...typeForm,
        company_id: 1,
        max_amount: typeForm.max_amount ? Number(typeForm.max_amount) : null,
      };
      if (editingType) {
        await api.patch(`/api/v1/reimbursements/types/${editingType.id}`, body);
      } else {
        await api.post('/api/v1/reimbursements/types', body);
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
      await api.delete(`/api/v1/reimbursements/types/${deleteTypeTarget.id}`);
      setDeleteTypeTarget(null);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    }
  };

  // ─── Reimbursement Claim Handlers ───────────────────────────────────────────

  const openAddReimbursementModal = () => {
    setEditingReimbursement(null);
    setReimbursementForm({
      ...EMPTY_REIMBURSEMENT_FORM,
      claim_date: new Date().toISOString().split('T')[0],
      expense_date: new Date().toISOString().split('T')[0],
    });
    setReimbursementFormError(null);
    setShowReimbursementModal(true);
  };

  const openEditReimbursementModal = (item: Reimbursement) => {
    setEditingReimbursement(item);
    setReimbursementForm({
      employee_id: String(item.employee_id),
      reimbursement_type_id: String(item.reimbursement_type_id),
      claim_amount: item.claim_amount,
      claim_date: item.claim_date,
      expense_date: item.expense_date,
      description: item.description || '',
      receipt_path: '',
    });
    setReimbursementFormError(null);
    setShowReimbursementModal(true);
  };

  const handleSaveReimbursement = async () => {
    setSavingReimbursement(true);
    setReimbursementFormError(null);
    try {
      const body = {
        employee_id: Number(reimbursementForm.employee_id),
        reimbursement_type_id: Number(reimbursementForm.reimbursement_type_id),
        claim_amount: Number(reimbursementForm.claim_amount),
        claim_date: reimbursementForm.claim_date,
        expense_date: reimbursementForm.expense_date,
        description: reimbursementForm.description || null,
        receipt_path: reimbursementForm.receipt_path || null,
      };
      if (editingReimbursement) {
        await api.patch(`/api/v1/reimbursements/${editingReimbursement.id}`, body);
      } else {
        await api.post('/api/v1/reimbursements', body);
      }
      setShowReimbursementModal(false);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setReimbursementFormError(err.message);
      } else {
        setReimbursementFormError('Terjadi kesalahan. Coba lagi.');
      }
    } finally {
      setSavingReimbursement(false);
    }
  };

  const handleDeleteReimbursement = async () => {
    if (!deleteReimbursementTarget) return;
    try {
      await api.delete(`/api/v1/reimbursements/${deleteReimbursementTarget.id}`);
      setDeleteReimbursementTarget(null);
      fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    }
  };

  const handleApproveReimbursement = async (
    reimbursement: Reimbursement,
    status: 'APPROVED' | 'REJECTED'
  ) => {
    try {
      await api.patch(`/api/v1/reimbursements/${reimbursement.id}`, {
        approval_status: status,
      });
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
          <h1 className="text-2xl font-bold text-gray-900">Reimbursement</h1>
          <p className="text-sm text-gray-500 mt-1">
            Kelola jenis reimbursement dan klaim penggantian biaya karyawan
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('records')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'records'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Data Klaim
          </button>
          <button
            onClick={() => setActiveTab('types')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'types'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Jenis Reimbursement
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="ml-2 text-sm text-gray-500">Memuat data...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12 bg-white rounded-xl border border-gray-200">
          <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
          <p className="text-sm text-gray-600 mb-3">{error}</p>
          <button
            onClick={fetchData}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Coba Lagi
          </button>
        </div>
      ) : activeTab === 'records' ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">Daftar Klaim Reimbursement</h2>
            <div className="flex items-center gap-2 flex-wrap">
              <ExcelActions module="reimbursements" companyId={1} onImportSuccess={fetchData} />
              <button
                onClick={openAddReimbursementModal}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Tambah Klaim
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Karyawan</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Jenis</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Klaim</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Disetujui</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Tgl Pengajuan</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {reimbursements.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-gray-500">
                      Belum ada data reimbursement.
                    </td>
                  </tr>
                ) : (
                  reimbursements.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-900">{item.employee_name}</td>
                      <td className="py-3 px-4 text-gray-600">{item.reimbursement_type_name}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatIDR(Number(item.claim_amount))}</td>
                      <td className="py-3 px-4 text-right font-mono">
                        {item.approved_amount ? formatIDR(Number(item.approved_amount)) : '-'}
                      </td>
                      <td className="py-3 px-4 text-gray-600">{item.claim_date}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(item.approval_status)}`}>
                          {item.approval_status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          {item.approval_status === 'PENDING' && !item.is_processed && (
                            <>
                              <button
                                onClick={() => handleApproveReimbursement(item, 'APPROVED')}
                                className="p-1.5 rounded-md hover:bg-emerald-50 text-slate-500 hover:text-emerald-600 transition-colors"
                                title="Approve"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleApproveReimbursement(item, 'REJECTED')}
                                className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-red-600 transition-colors"
                                title="Reject"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => openEditReimbursementModal(item)}
                            className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-blue-600 transition-colors"
                            title="Edit"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeleteReimbursementTarget(item)}
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
            <h2 className="text-base font-semibold text-gray-900">Jenis Reimbursement</h2>
            <button
              onClick={openAddTypeModal}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
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
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Maksimum</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Kena Pajak</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {reimbursementTypes.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-gray-500">
                      Belum ada jenis reimbursement.
                    </td>
                  </tr>
                ) : (
                  reimbursementTypes.map((type) => (
                    <tr key={type.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-900 font-medium">{type.name}</td>
                      <td className="py-3 px-4 font-mono text-gray-700">{type.code}</td>
                      <td className="py-3 px-4 text-right font-mono">
                        {type.max_amount ? formatIDR(Number(type.max_amount)) : '-'}
                      </td>
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
                            className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-blue-600 transition-colors"
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

      {/* ─── Reimbursement Modal ─────────────────────────────────────────────── */}
      {showReimbursementModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowReimbursementModal(false)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingReimbursement ? 'Edit' : 'Tambah'} Klaim Reimbursement
              </h3>
              <button onClick={() => setShowReimbursementModal(false)} className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <EmployeeSearchSelect
                employees={employees}
                value={reimbursementForm.employee_id}
                onChange={(value) => setReimbursementForm({ ...reimbursementForm, employee_id: value })}
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jenis Reimbursement</label>
                <select
                  value={reimbursementForm.reimbursement_type_id}
                  onChange={(e) => setReimbursementForm({ ...reimbursementForm, reimbursement_type_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Pilih Jenis</option>
                  {reimbursementTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jumlah Klaim</label>
                <input
                  type="number"
                  value={reimbursementForm.claim_amount}
                  onChange={(e) => setReimbursementForm({ ...reimbursementForm, claim_amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Contoh: 1500000"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tgl Pengajuan</label>
                  <input
                    type="date"
                    value={reimbursementForm.claim_date}
                    onChange={(e) => setReimbursementForm({ ...reimbursementForm, claim_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tgl Pengeluaran</label>
                  <input
                    type="date"
                    value={reimbursementForm.expense_date}
                    onChange={(e) => setReimbursementForm({ ...reimbursementForm, expense_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Keterangan</label>
                <textarea
                  value={reimbursementForm.description}
                  onChange={(e) => setReimbursementForm({ ...reimbursementForm, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bukti/Bill (URL)</label>
                <input
                  type="text"
                  value={reimbursementForm.receipt_path}
                  onChange={(e) => setReimbursementForm({ ...reimbursementForm, receipt_path: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Contoh: https://storage/.../receipt.pdf"
                />
              </div>
            </div>

            {reimbursementFormError && (
              <div className="mt-3 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {reimbursementFormError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setShowReimbursementModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleSaveReimbursement}
                disabled={savingReimbursement}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {savingReimbursement && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Reimbursement Type Modal ────────────────────────────────────────── */}
      {showTypeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowTypeModal(false)} />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingType ? 'Edit' : 'Tambah'} Jenis Reimbursement
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Contoh: Transportasi"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Kode</label>
                <input
                  type="text"
                  value={typeForm.code}
                  onChange={(e) => setTypeForm({ ...typeForm, code: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Contoh: RMB-TRANSPORT"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Maksimum Klaim (kosong = tidak dibatasi)</label>
                <input
                  type="number"
                  value={typeForm.max_amount}
                  onChange={(e) => setTypeForm({ ...typeForm, max_amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Contoh: 500000"
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={typeForm.is_taxable}
                    onChange={(e) => setTypeForm({ ...typeForm, is_taxable: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  Kena Pajak
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={typeForm.is_active}
                    onChange={(e) => setTypeForm({ ...typeForm, is_active: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
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
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {savingType && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Delete Confirmation ─────────────────────────────────────────────── */}
      {(deleteReimbursementTarget || deleteTypeTarget) && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/30" onClick={() => { setDeleteReimbursementTarget(null); setDeleteTypeTarget(null); }} />
          <div className="relative bg-white rounded-xl shadow-xl border border-red-100 p-6 w-full max-w-sm mx-4">
            <h4 className="text-base font-semibold text-gray-900 mb-2">Konfirmasi Hapus</h4>
            <p className="text-sm text-gray-600 mb-4">
              Hapus <span className="font-semibold">{deleteReimbursementTarget?.employee_name || deleteTypeTarget?.name}</span>?
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => { setDeleteReimbursementTarget(null); setDeleteTypeTarget(null); }}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={() => {
                  if (deleteReimbursementTarget) handleDeleteReimbursement();
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
