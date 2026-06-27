'use client';

import { useState, useEffect } from 'react';
import { api, ApiError } from '@/lib/api';
import { RuleCategory, RuleConfiguration, RuleAuditLog, RuleType } from '@/types';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { Loader2, Plus, Trash2, History, RotateCcw } from 'lucide-react';

interface FormData {
  category_id: number;
  rule_code: string;
  rule_name: string;
  rule_type: RuleType;
  formula: string;
  value: string;
  min_value: string;
  max_value: string;
  rate: string;
  effective_date: string;
  expiry_date: string;
  priority: string;
  description: string;
}

const RULE_TYPES: RuleType[] = ['CONSTANT', 'FORMULA', 'BRACKET', 'LOOKUP_TABLE'];

const emptyForm: FormData = {
  category_id: 0,
  rule_code: '',
  rule_name: '',
  rule_type: 'CONSTANT',
  formula: '',
  value: '',
  min_value: '',
  max_value: '',
  rate: '',
  effective_date: '',
  expiry_date: '',
  priority: '0',
  description: '',
};

export default function RulesSettingsPage() {
  const [categories, setCategories] = useState<RuleCategory[]>([]);
  const [rules, setRules] = useState<RuleConfiguration[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<RuleConfiguration | null>(null);
  const [formData, setFormData] = useState<FormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [auditRule, setAuditRule] = useState<RuleConfiguration | null>(null);
  const [auditLogs, setAuditLogs] = useState<RuleAuditLog[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const selectedCategory = categories.find((c) => c.id === selectedCategoryId) || null;

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    if (selectedCategoryId) {
      fetchRules(selectedCategoryId);
    } else {
      setRules([]);
    }
  }, [selectedCategoryId]);

  const fetchCategories = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<RuleCategory[]>('/api/v1/admin/rules/categories');
      setCategories(data);
      if (data.length && !selectedCategoryId) {
        setSelectedCategoryId(data[0].id);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Gagal memuat kategori aturan');
    } finally {
      setLoading(false);
    }
  };

  const fetchRules = async (categoryId: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<RuleConfiguration[]>(
        `/api/v1/admin/rules/configurations?company_id=1&category_id=${categoryId}`
      );
      setRules(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Gagal memuat aturan');
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    setEditingRule(null);
    setFormData({
      ...emptyForm,
      category_id: selectedCategoryId || 0,
      effective_date: new Date().toISOString().split('T')[0],
    });
    setIsModalOpen(true);
  };

  const openEditModal = (rule: RuleConfiguration) => {
    setEditingRule(rule);
    setFormData({
      category_id: rule.category_id,
      rule_code: rule.rule_code,
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      formula: rule.formula || '',
      value: rule.value !== null ? String(rule.value) : '',
      min_value: rule.min_value !== null ? String(rule.min_value) : '',
      max_value: rule.max_value !== null ? String(rule.max_value) : '',
      rate: rule.rate !== null ? String(rule.rate) : '',
      effective_date: rule.effective_date,
      expiry_date: rule.expiry_date || '',
      priority: String(rule.priority),
      description: rule.description || '',
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingRule(null);
    setFormData(emptyForm);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        company_id: 1,
        category_id: Number(formData.category_id),
        rule_code: formData.rule_code,
        rule_name: formData.rule_name,
        rule_type: formData.rule_type,
        formula: formData.formula || null,
        value: formData.value ? Number(formData.value) : null,
        min_value: formData.min_value ? Number(formData.min_value) : null,
        max_value: formData.max_value ? Number(formData.max_value) : null,
        rate: formData.rate ? Number(formData.rate) : null,
        effective_date: formData.effective_date,
        expiry_date: formData.expiry_date || null,
        priority: Number(formData.priority) || 0,
        description: formData.description || null,
      };

      if (editingRule) {
        await api.patch(`/api/v1/admin/rules/configurations/${editingRule.id}`, payload);
      } else {
        await api.post('/api/v1/admin/rules/configurations', payload);
      }
      closeModal();
      if (selectedCategoryId) fetchRules(selectedCategoryId);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menyimpan aturan');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (rule: RuleConfiguration) => {
    if (!confirm(`Hapus aturan ${rule.rule_code}?`)) return;
    try {
      await api.delete(`/api/v1/admin/rules/configurations/${rule.id}`);
      if (selectedCategoryId) fetchRules(selectedCategoryId);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menghapus aturan');
    }
  };

  const handleToggleActive = async (rule: RuleConfiguration) => {
    try {
      await api.patch(`/api/v1/admin/rules/configurations/${rule.id}`, {
        is_active: !rule.is_active,
      });
      if (selectedCategoryId) fetchRules(selectedCategoryId);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal mengubah status aturan');
    }
  };

  const handleReset = async () => {
    if (!selectedCategoryId) return;
    if (!confirm('Nonaktifkan semua aturan custom di kategori ini?')) return;
    try {
      await api.post('/api/v1/admin/rules/reset-to-default', {
        company_id: 1,
        category_id: selectedCategoryId,
      });
      fetchRules(selectedCategoryId);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal reset aturan');
    }
  };

  const openAudit = async (rule: RuleConfiguration) => {
    setAuditRule(rule);
    setAuditLoading(true);
    try {
      const data = await api.get<RuleAuditLog[]>(
        `/api/v1/admin/rules/configurations/${rule.id}/audit-logs`
      );
      setAuditLogs(data);
    } catch (err) {
      setAuditLogs([]);
    } finally {
      setAuditLoading(false);
    }
  };

  const renderValueFields = () => {
    switch (formData.rule_type) {
      case 'CONSTANT':
      case 'LOOKUP_TABLE':
        return (
          <Input
            label="Nilai"
            type="number"
            value={formData.value}
            onChange={(e) => setFormData({ ...formData, value: e.target.value })}
          />
        );
      case 'FORMULA':
        return (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Formula</label>
              <textarea
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                rows={3}
                value={formData.formula}
                onChange={(e) => setFormData({ ...formData, formula: e.target.value })}
                placeholder="Contoh: basic_salary * 0.01"
              />
            </div>
          </div>
        );
      case 'BRACKET':
        return (
          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Min"
              type="number"
              value={formData.min_value}
              onChange={(e) => setFormData({ ...formData, min_value: e.target.value })}
            />
            <Input
              label="Max"
              type="number"
              value={formData.max_value}
              onChange={(e) => setFormData({ ...formData, max_value: e.target.value })}
            />
            <Input
              label="Rate"
              type="number"
              step="0.0001"
              value={formData.rate}
              onChange={(e) => setFormData({ ...formData, rate: e.target.value })}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Rules Engine</h1>
        <p className="text-sm text-gray-500">
          Aturan kustom akan menggantikan konfigurasi standar jika aktif.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 md:col-span-3 space-y-3">
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Kategori</h2>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategoryId(cat.id)}
              className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                selectedCategoryId === cat.id
                  ? 'bg-cyan-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
              }`}
            >
              {cat.category_name}
            </button>
          ))}
        </div>

        <div className="col-span-12 md:col-span-9 space-y-4">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {selectedCategory
                  ? `Aturan Kustom: ${selectedCategory.category_name}`
                  : 'Pilih Kategori'}
              </h2>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  onClick={handleReset}
                  disabled={!selectedCategoryId || loading}
                  className="flex items-center gap-2"
                >
                  <RotateCcw className="w-4 h-4" /> Reset
                </Button>
                <Button
                  onClick={openCreateModal}
                  disabled={!selectedCategoryId || loading}
                  className="flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" /> Tambah Aturan
                </Button>
              </div>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-cyan-600" />
              </div>
            ) : rules.length === 0 ? (
              <div className="text-center py-12 text-gray-500 text-sm">
                Belum ada aturan kustom. Gunakan tombol Tambah Aturan untuk override konfigurasi.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm text-left">
                  <thead className="bg-gray-50 text-gray-700 font-medium">
                    <tr>
                      <th className="px-4 py-2">Kode</th>
                      <th className="px-4 py-2">Nama</th>
                      <th className="px-4 py-2">Tipe</th>
                      <th className="px-4 py-2">Nilai/Formula</th>
                      <th className="px-4 py-2">Efektif</th>
                      <th className="px-4 py-2">Status</th>
                      <th className="px-4 py-2 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rules.map((rule) => (
                      <tr key={rule.id}>
                        <td className="px-4 py-2 font-medium text-gray-900">{rule.rule_code}</td>
                        <td className="px-4 py-2">{rule.rule_name}</td>
                        <td className="px-4 py-2">{rule.rule_type}</td>
                        <td className="px-4 py-2">
                          {rule.formula ||
                            (rule.value !== null ? rule.value : '-')}
                        </td>
                        <td className="px-4 py-2">{rule.effective_date}</td>
                        <td className="px-4 py-2">
                          <button
                            onClick={() => handleToggleActive(rule)}
                            className={`px-2 py-1 rounded text-xs font-medium ${
                              rule.is_active
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {rule.is_active ? 'Aktif' : 'Nonaktif'}
                          </button>
                        </td>
                        <td className="px-4 py-2 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => openAudit(rule)}
                              className="p-1 text-gray-500 hover:text-cyan-600"
                              title="Audit Trail"
                            >
                              <History className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => openEditModal(rule)}
                              className="text-cyan-600 hover:text-cyan-700 font-medium"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDelete(rule)}
                              className="p-1 text-red-500 hover:text-red-600"
                              title="Hapus"
                            >
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
          </Card>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {editingRule ? 'Edit Aturan' : 'Tambah Aturan'}
                </h3>
                <button onClick={closeModal} className="text-gray-400 hover:text-gray-600">
                  &times;
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Rule Code"
                  value={formData.rule_code}
                  onChange={(e) => setFormData({ ...formData, rule_code: e.target.value })}
                  placeholder="BPJS_KES_EMPLOYEE_RATE"
                />
                <Input
                  label="Rule Name"
                  value={formData.rule_name}
                  onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                  placeholder="BPJS Kesehatan Employee Rate"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipe</label>
                  <select
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={formData.rule_type}
                    onChange={(e) => setFormData({ ...formData, rule_type: e.target.value as RuleType })}
                  >
                    {RULE_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <Input
                  label="Prioritas"
                  type="number"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                />
              </div>

              {renderValueFields()}

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Tanggal Efektif"
                  type="date"
                  value={formData.effective_date}
                  onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
                />
                <Input
                  label="Tanggal Expired (opsional)"
                  type="date"
                  value={formData.expiry_date}
                  onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Deskripsi</label>
                <textarea
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="secondary" onClick={closeModal}>
                  Batal
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={
                    saving ||
                    !formData.rule_code ||
                    !formData.rule_name ||
                    !formData.effective_date
                  }
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Simpan'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {auditRule && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Audit Trail: {auditRule.rule_code}
                </h3>
                <button
                  onClick={() => setAuditRule(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  &times;
                </button>
              </div>

              {auditLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-cyan-600" />
                </div>
              ) : auditLogs.length === 0 ? (
                <div className="text-center py-8 text-gray-500 text-sm">
                  Belum ada audit log.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm text-left">
                    <thead className="bg-gray-50 text-gray-700 font-medium">
                      <tr>
                        <th className="px-4 py-2">Aksi</th>
                        <th className="px-4 py-2">Oleh</th>
                        <th className="px-4 py-2">Waktu</th>
                        <th className="px-4 py-2">Alasan</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {auditLogs.map((log) => (
                        <tr key={log.id}>
                          <td className="px-4 py-2">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              log.action === 'CREATE'
                                ? 'bg-green-100 text-green-700'
                                : log.action === 'DELETE'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-blue-100 text-blue-700'
                            }`}>
                              {log.action}
                            </span>
                          </td>
                          <td className="px-4 py-2">{log.changed_by_name || log.changed_by}</td>
                          <td className="px-4 py-2">
                            {new Date(log.changed_at).toLocaleString('id-ID')}
                          </td>
                          <td className="px-4 py-2">{log.reason || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
