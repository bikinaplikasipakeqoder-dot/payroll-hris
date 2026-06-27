'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Plus,
  Pencil,
  Trash2,
  X,
  Building2,
  Briefcase,
  Award,
  UserCheck,
  Loader2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Department {
  id: number;
  company_id: number;
  code: string;
  name: string;
}

interface Position {
  id: number;
  company_id: number;
  code: string;
  name: string;
}

interface Grade {
  id: number;
  company_id: number;
  grade_code: string;
  grade_name: string;
}

interface EmploymentStatus {
  id: number;
  company_id: number;
  name: string;
  code: string;
}

type TabKey = 'departments' | 'positions' | 'grades' | 'employment-statuses';

interface TabConfig {
  key: TabKey;
  label: string;
  icon: typeof Building2;
}

const TABS: TabConfig[] = [
  { key: 'departments', label: 'Departemen', icon: Building2 },
  { key: 'positions', label: 'Jabatan', icon: Briefcase },
  { key: 'grades', label: 'Grade', icon: Award },
  { key: 'employment-statuses', label: 'Status Kepegawaian', icon: UserCheck },
];

// ─── Component ───────────────────────────────────────────────────────────────

export default function MasterDataPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('departments');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<any | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // ─── Data Fetching ──────────────────────────────────────────────────────────

  const fetchData = useCallback(async (tab: TabKey) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<any[]>(`/api/v1/master-data/${tab}?company_id=1`);
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
    fetchData(activeTab);
  }, [activeTab, fetchData]);

  // ─── CRUD Handlers ──────────────────────────────────────────────────────────

  const openAddModal = () => {
    setEditingItem(null);
    setFormData(getEmptyForm(activeTab));
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (item: any) => {
    setEditingItem(item);
    setFormData(getFormFromItem(activeTab, item));
    setFormError(null);
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);
    try {
      if (editingItem) {
        const body = buildPatchBody(activeTab, formData);
        await api.patch(`/api/v1/master-data/${activeTab}/${editingItem.id}`, body);
      } else {
        const body = buildCreateBody(activeTab, formData);
        await api.post(`/api/v1/master-data/${activeTab}`, body);
      }
      setShowModal(false);
      fetchData(activeTab);
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
      await api.delete(`/api/v1/master-data/${activeTab}/${deleteTarget.id}`);
      setDeleteTarget(null);
      fetchData(activeTab);
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setDeleteError('Tidak dapat dihapus: data sedang digunakan oleh karyawan.');
      } else if (err instanceof ApiError) {
        setDeleteError(err.message);
      } else {
        setDeleteError('Terjadi kesalahan. Coba lagi.');
      }
    } finally {
      setDeleting(false);
    }
  };

  // ─── Form Helpers ───────────────────────────────────────────────────────────

  function getEmptyForm(tab: TabKey): Record<string, string> {
    switch (tab) {
      case 'departments':
        return { code: '', name: '' };
      case 'positions':
        return { code: '', name: '' };
      case 'grades':
        return { grade_code: '', grade_name: '' };
      case 'employment-statuses':
        return { code: '', name: '' };
    }
  }

  function getFormFromItem(tab: TabKey, item: any): Record<string, string> {
    switch (tab) {
      case 'departments':
        return { code: item.code, name: item.name };
      case 'positions':
        return { code: item.code, name: item.name };
      case 'grades':
        return {
          grade_code: item.grade_code,
          grade_name: item.grade_name,
        };
      case 'employment-statuses':
        return { code: item.code, name: item.name };
    }
  }

  function buildCreateBody(tab: TabKey, form: Record<string, string>) {
    const base = { company_id: 1 };
    switch (tab) {
      case 'departments':
        return { ...base, code: form.code, name: form.name };
      case 'positions':
        return { ...base, code: form.code, name: form.name };
      case 'grades':
        return {
          ...base,
          grade_code: form.grade_code,
          grade_name: form.grade_name,
        };
      case 'employment-statuses':
        return { ...base, code: form.code, name: form.name };
    }
  }

  function buildPatchBody(tab: TabKey, form: Record<string, string>) {
    switch (tab) {
      case 'departments':
        return { code: form.code, name: form.name };
      case 'positions':
        return { code: form.code, name: form.name };
      case 'grades':
        return {
          grade_code: form.grade_code,
          grade_name: form.grade_name,
        };
      case 'employment-statuses':
        return { code: form.code, name: form.name };
    }
  }

  function getEntityLabel(tab: TabKey): string {
    switch (tab) {
      case 'departments': return 'Departemen';
      case 'positions': return 'Jabatan';
      case 'grades': return 'Grade';
      case 'employment-statuses': return 'Status Kepegawaian';
    }
  }

  function getDeleteName(item: any): string {
    return item.name || item.grade_name || item.code || '';
  }

  // ─── Render Table ───────────────────────────────────────────────────────────

  const renderTable = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="ml-2 text-sm text-slate-500">Memuat data...</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
          <p className="text-sm text-slate-600 mb-3">{error}</p>
          <button
            onClick={() => fetchData(activeTab)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Coba Lagi
          </button>
        </div>
      );
    }

    if (data.length === 0) {
      return (
        <div className="text-center py-12 text-sm text-slate-500">
          Belum ada data. Klik &quot;Tambah {getEntityLabel(activeTab)}&quot; untuk menambahkan.
        </div>
      );
    }

    switch (activeTab) {
      case 'departments':
        return (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-slate-600">Kode</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Nama</th>
                <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(data as Department[]).map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4 font-mono text-slate-700">{item.code}</td>
                  <td className="py-3 px-4 text-slate-800">{item.name}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-blue-600 transition-colors" title="Edit">
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
        );

      case 'positions':
        return (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-slate-600">Kode</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Nama</th>
                <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(data as Position[]).map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4 font-mono text-slate-700">{item.code}</td>
                  <td className="py-3 px-4 text-slate-800">{item.name}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-blue-600 transition-colors" title="Edit">
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
        );

      case 'grades':
        return (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-slate-600">Kode Grade</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Nama Grade</th>
                <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(data as Grade[]).map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4 font-mono text-slate-700">{item.grade_code}</td>
                  <td className="py-3 px-4 text-slate-800">{item.grade_name}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-blue-600 transition-colors" title="Edit">
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
        );

      case 'employment-statuses':
        return (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-slate-600">Kode</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Nama</th>
                <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(data as EmploymentStatus[]).map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4 font-mono text-slate-700">{item.code}</td>
                  <td className="py-3 px-4 text-slate-800 font-medium">{item.name}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-blue-600 transition-colors" title="Edit">
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
        );
    }
  };

  // ─── Render Form Fields ─────────────────────────────────────────────────────

  const renderFormFields = () => {
    switch (activeTab) {
      case 'departments':
        return (
          <>
            <FormField label="Kode" value={formData.code} onChange={(v) => setFormData({ ...formData, code: v })} placeholder="Contoh: DEPT-001" />
            <FormField label="Nama" value={formData.name} onChange={(v) => setFormData({ ...formData, name: v })} placeholder="Contoh: Human Resource" />
          </>
        );
      case 'positions':
        return (
          <>
            <FormField label="Kode" value={formData.code} onChange={(v) => setFormData({ ...formData, code: v })} placeholder="Contoh: POS-001" />
            <FormField label="Nama" value={formData.name} onChange={(v) => setFormData({ ...formData, name: v })} placeholder="Contoh: Manager" />
          </>
        );
      case 'grades':
        return (
          <>
            <FormField label="Kode Grade" value={formData.grade_code} onChange={(v) => setFormData({ ...formData, grade_code: v })} placeholder="Contoh: G1" />
            <FormField label="Nama Grade" value={formData.grade_name} onChange={(v) => setFormData({ ...formData, grade_name: v })} placeholder="Contoh: Grade 1" />
          </>
        );
      case 'employment-statuses':
        return (
          <>
            <FormField label="Kode" value={formData.code} onChange={(v) => setFormData({ ...formData, code: v })} placeholder="Contoh: TETAP" />
            <FormField label="Nama" value={formData.name} onChange={(v) => setFormData({ ...formData, name: v })} placeholder="Contoh: Karyawan Tetap" />
          </>
        );
    }
  };

  // ─── Main Render ────────────────────────────────────────────────────────────

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
            className="border-b-2 border-blue-500 text-blue-600 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Master Data
          </Link>
        </nav>
      </div>

      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Master Data</h1>
        <p className="text-sm text-slate-500 mt-1">
          Kelola data referensi perusahaan
        </p>
      </div>

      {/* Entity Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-6">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`inline-flex items-center gap-2 whitespace-nowrap py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {/* Card Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-slate-800">
            {getEntityLabel(activeTab)}
          </h2>
          <button
            onClick={openAddModal}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Tambah {getEntityLabel(activeTab)}
          </button>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          {renderTable()}
        </div>
      </div>

      {/* ─── Add/Edit Modal ──────────────────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-800">
                {editingItem ? 'Edit' : 'Tambah'} {getEntityLabel(activeTab)}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded-md hover:bg-gray-100 text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {renderFormFields()}
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
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
              Apakah Anda yakin ingin menghapus <span className="font-semibold text-slate-800">{getDeleteName(deleteTarget)}</span>?
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
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        placeholder={placeholder}
      />
    </div>
  );
}
