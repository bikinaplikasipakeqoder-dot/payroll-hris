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

type TabKey = 'method' | 'ptkp' | 'brackets' | 'ter';

interface TabConfig {
  key: TabKey;
  label: string;
}

const TABS: TabConfig[] = [
  { key: 'method', label: 'Metode' },
  { key: 'ptkp', label: 'PTKP' },
  { key: 'brackets', label: 'Bracket Pasal 17' },
  { key: 'ter', label: 'Bracket TER' },
];

const PAYROLL_METHOD_LABELS: Record<'GROSS' | 'GROSS_UP' | 'NETT', string> = {
  GROSS: 'Gross',
  GROSS_UP: 'Gross Up',
  NETT: 'Nett',
};

interface TaxSetting {
  id: number;
  company_id: number;
  tax_calculation_method: 'PASAL_17' | 'TER';
  payroll_method: 'GROSS' | 'GROSS_UP' | 'NETT';
  is_active: boolean;
}

interface PtkpValue {
  id: number;
  company_id: number;
  ptkp_code: string;
  description: string;
  annual_amount: string;
  monthly_amount: string;
  regulation_year: number;
  regulation_reference: string | null;
  effective_date: string;
  end_date: string | null;
  is_active: boolean;
}

interface TaxBracket {
  id: number;
  company_id: number;
  bracket_order: number;
  income_range_min: string;
  income_range_max: string | null;
  tax_rate: string;
  regulation_year: number;
  effective_date: string;
  end_date: string | null;
  is_active: boolean;
}

interface TerBracket {
  id: number;
  company_id: number;
  category: 'A' | 'B' | 'C';
  income_range_min: string;
  income_range_max: string | null;
  ter_rate: string;
  regulation_year: number;
  effective_date: string;
  end_date: string | null;
  is_active: boolean;
}

interface MethodForm {
  tax_calculation_method: 'PASAL_17' | 'TER';
  payroll_method: 'GROSS' | 'GROSS_UP' | 'NETT';
  is_active: boolean;
}

interface PtkpForm {
  ptkp_code: string;
  description: string;
  annual_amount: string;
  monthly_amount: string;
  regulation_year: string;
  regulation_reference: string;
  effective_date: string;
  end_date: string;
  is_active: boolean;
}

interface BracketForm {
  bracket_order: string;
  income_range_min: string;
  income_range_max: string;
  tax_rate: string;
  regulation_year: string;
  effective_date: string;
  end_date: string;
  is_active: boolean;
}

interface TerForm {
  category: 'A' | 'B' | 'C';
  income_range_min: string;
  income_range_max: string;
  ter_rate: string;
  regulation_year: string;
  effective_date: string;
  end_date: string;
  is_active: boolean;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function TaxSettingsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('method');

  const [methodData, setMethodData] = useState<TaxSetting[]>([]);
  const [ptkpData, setPtkpData] = useState<PtkpValue[]>([]);
  const [bracketData, setBracketData] = useState<TaxBracket[]>([]);
  const [terData, setTerData] = useState<TerBracket[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [methodForm, setMethodForm] = useState<MethodForm>({ tax_calculation_method: 'PASAL_17', payroll_method: 'GROSS', is_active: true });
  const [ptkpForm, setPtkpForm] = useState<PtkpForm>({
    ptkp_code: '',
    description: '',
    annual_amount: '',
    monthly_amount: '',
    regulation_year: String(new Date().getFullYear()),
    regulation_reference: '',
    effective_date: new Date().toISOString().split('T')[0],
    end_date: '',
    is_active: true,
  });
  const [bracketForm, setBracketForm] = useState<BracketForm>({
    bracket_order: '',
    income_range_min: '',
    income_range_max: '',
    tax_rate: '',
    regulation_year: String(new Date().getFullYear()),
    effective_date: new Date().toISOString().split('T')[0],
    end_date: '',
    is_active: true,
  });
  const [terForm, setTerForm] = useState<TerForm>({
    category: 'A',
    income_range_min: '',
    income_range_max: '',
    ter_rate: '',
    regulation_year: String(new Date().getFullYear()),
    effective_date: new Date().toISOString().split('T')[0],
    end_date: '',
    is_active: true,
  });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<any>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // ─── Data Fetching ──────────────────────────────────────────────────────────

  const fetchData = useCallback(async (tab: TabKey) => {
    setLoading(true);
    setError(null);
    try {
      if (tab === 'method') {
        const result = await api.get<TaxSetting[]>('/api/v1/tax/settings?company_id=1');
        setMethodData(result);
      } else if (tab === 'ptkp') {
        const result = await api.get<PtkpValue[]>('/api/v1/tax/ptkp?company_id=1');
        setPtkpData(result);
      } else if (tab === 'brackets') {
        const result = await api.get<TaxBracket[]>('/api/v1/tax/brackets?company_id=1');
        setBracketData(result);
      } else if (tab === 'ter') {
        const result = await api.get<TerBracket[]>('/api/v1/tax/ter-brackets?company_id=1');
        setTerData(result);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Gagal memuat data: ${err.message}`);
      } else {
        setError('Tidak dapat terhubung ke server. Pastikan backend sedang berjalan.');
      }
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
    resetForms();
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (item: any) => {
    setEditingItem(item);
    setFormError(null);
    if (activeTab === 'method') {
      setMethodForm({
        tax_calculation_method: item.tax_calculation_method,
        payroll_method: item.payroll_method,
        is_active: item.is_active,
      });
    } else if (activeTab === 'ptkp') {
      setPtkpForm({
        ptkp_code: item.ptkp_code,
        description: item.description,
        annual_amount: item.annual_amount,
        monthly_amount: item.monthly_amount,
        regulation_year: String(item.regulation_year),
        regulation_reference: item.regulation_reference || '',
        effective_date: item.effective_date,
        end_date: item.end_date || '',
        is_active: item.is_active,
      });
    } else if (activeTab === 'brackets') {
      setBracketForm({
        bracket_order: String(item.bracket_order),
        income_range_min: item.income_range_min,
        income_range_max: item.income_range_max || '',
        tax_rate: item.tax_rate,
        regulation_year: String(item.regulation_year),
        effective_date: item.effective_date,
        end_date: item.end_date || '',
        is_active: item.is_active,
      });
    } else if (activeTab === 'ter') {
      setTerForm({
        category: item.category,
        income_range_min: item.income_range_min,
        income_range_max: item.income_range_max || '',
        ter_rate: item.ter_rate,
        regulation_year: String(item.regulation_year),
        effective_date: item.effective_date,
        end_date: item.end_date || '',
        is_active: item.is_active,
      });
    }
    setShowModal(true);
  };

  const resetForms = () => {
    setMethodForm({ tax_calculation_method: 'PASAL_17', payroll_method: 'GROSS', is_active: true });
    setPtkpForm({
      ptkp_code: '',
      description: '',
      annual_amount: '',
      monthly_amount: '',
      regulation_year: String(new Date().getFullYear()),
      regulation_reference: '',
      effective_date: new Date().toISOString().split('T')[0],
      end_date: '',
      is_active: true,
    });
    setBracketForm({
      bracket_order: '',
      income_range_min: '',
      income_range_max: '',
      tax_rate: '',
      regulation_year: String(new Date().getFullYear()),
      effective_date: new Date().toISOString().split('T')[0],
      end_date: '',
      is_active: true,
    });
    setTerForm({
      category: 'A',
      income_range_min: '',
      income_range_max: '',
      ter_rate: '',
      regulation_year: String(new Date().getFullYear()),
      effective_date: new Date().toISOString().split('T')[0],
      end_date: '',
      is_active: true,
    });
  };

  const buildBody = () => {
    if (activeTab === 'method') {
      return {
        tax_calculation_method: methodForm.tax_calculation_method,
        payroll_method: methodForm.payroll_method,
        is_active: methodForm.is_active,
      };
    }
    if (activeTab === 'ptkp') {
      return {
        company_id: 1,
        ptkp_code: ptkpForm.ptkp_code,
        description: ptkpForm.description,
        annual_amount: ptkpForm.annual_amount,
        monthly_amount: ptkpForm.monthly_amount,
        regulation_year: Number(ptkpForm.regulation_year),
        regulation_reference: ptkpForm.regulation_reference || null,
        effective_date: ptkpForm.effective_date,
        end_date: ptkpForm.end_date || null,
        is_active: ptkpForm.is_active,
      };
    }
    if (activeTab === 'brackets') {
      return {
        company_id: 1,
        bracket_order: Number(bracketForm.bracket_order),
        income_range_min: bracketForm.income_range_min,
        income_range_max: bracketForm.income_range_max || null,
        tax_rate: bracketForm.tax_rate,
        regulation_year: Number(bracketForm.regulation_year),
        effective_date: bracketForm.effective_date,
        end_date: bracketForm.end_date || null,
        is_active: bracketForm.is_active,
      };
    }
    return {
      company_id: 1,
      category: terForm.category,
      income_range_min: terForm.income_range_min,
      income_range_max: terForm.income_range_max || null,
      ter_rate: terForm.ter_rate,
      regulation_year: Number(terForm.regulation_year),
      effective_date: terForm.effective_date,
      end_date: terForm.end_date || null,
      is_active: terForm.is_active,
    };
  };

  const getEndpoint = () => {
    if (activeTab === 'method') return '/api/v1/tax/settings';
    if (activeTab === 'ptkp') return '/api/v1/tax/ptkp';
    if (activeTab === 'brackets') return '/api/v1/tax/brackets';
    return '/api/v1/tax/ter-brackets';
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError(null);
    try {
      if (editingItem) {
        await api.patch(`${getEndpoint()}/${editingItem.id}`, buildBody());
      } else {
        await api.post(getEndpoint(), buildBody());
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
      await api.delete(`${getEndpoint()}/${deleteTarget.id}`);
      setDeleteTarget(null);
      fetchData(activeTab);
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

  // ─── Render Table ───────────────────────────────────────────────────────────

  const renderTable = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-amber-600" />
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
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-amber-600 border border-amber-300 rounded-lg hover:bg-amber-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Coba Lagi
          </button>
        </div>
      );
    }

    if (activeTab === 'method') {
      if (methodData.length === 0) {
        return (
          <div className="text-center py-12 text-sm text-slate-500">
            Belum ada pengaturan metode pajak. Klik &quot;Tambah Metode&quot; untuk menambahkan.
          </div>
        );
      }
      return (
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-slate-600">Metode Perhitungan</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600">Metode Penggajian</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600">Status</th>
              <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {methodData.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="py-3 px-4 text-slate-800 font-medium">{item.tax_calculation_method}</td>
                <td className="py-3 px-4 text-slate-700">{PAYROLL_METHOD_LABELS[item.payroll_method]}</td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${item.is_active ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'}`}>
                    {item.is_active ? 'Aktif' : 'Nonaktif'}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-amber-50 text-slate-500 hover:text-amber-600 transition-colors" title="Edit">
                      <Pencil className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    if (activeTab === 'ptkp') {
      if (ptkpData.length === 0) {
        return (
          <div className="text-center py-12 text-sm text-slate-500">
            Belum ada data PTKP. Klik &quot;Tambah PTKP&quot; untuk menambahkan.
          </div>
        );
      }
      return (
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-slate-600">Kode</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600">Deskripsi</th>
              <th className="text-right py-3 px-4 font-medium text-slate-600">Tahunan</th>
              <th className="text-right py-3 px-4 font-medium text-slate-600">Bulanan</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600">Efektif</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600">Status</th>
              <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {ptkpData.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="py-3 px-4 font-mono text-slate-700">{item.ptkp_code}</td>
                <td className="py-3 px-4 text-slate-800">{item.description}</td>
                <td className="py-3 px-4 text-right text-slate-600">{Number(item.annual_amount).toLocaleString('id-ID')}</td>
                <td className="py-3 px-4 text-right text-slate-600">{Number(item.monthly_amount).toLocaleString('id-ID')}</td>
                <td className="py-3 px-4 text-slate-600">{item.effective_date}</td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${item.is_active ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'}`}>
                    {item.is_active ? 'Aktif' : 'Nonaktif'}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-amber-50 text-slate-500 hover:text-amber-600 transition-colors" title="Edit">
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

    if (activeTab === 'brackets') {
      if (bracketData.length === 0) {
        return (
          <div className="text-center py-12 text-sm text-slate-500">
            Belum ada bracket Pasal 17. Klik &quot;Tambah Bracket&quot; untuk menambahkan.
          </div>
        );
      }
      return (
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-slate-600">Urutan</th>
              <th className="text-right py-3 px-4 font-medium text-slate-600">Min</th>
              <th className="text-right py-3 px-4 font-medium text-slate-600">Maks</th>
              <th className="text-right py-3 px-4 font-medium text-slate-600">Tarif (%)</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600">Efektif</th>
              <th className="text-left py-3 px-4 font-medium text-slate-600">Status</th>
              <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {bracketData.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="py-3 px-4 text-slate-800 font-medium">{item.bracket_order}</td>
                <td className="py-3 px-4 text-right text-slate-600">{Number(item.income_range_min).toLocaleString('id-ID')}</td>
                <td className="py-3 px-4 text-right text-slate-600">{item.income_range_max ? Number(item.income_range_max).toLocaleString('id-ID') : '∞'}</td>
                <td className="py-3 px-4 text-right text-slate-600">{item.tax_rate}</td>
                <td className="py-3 px-4 text-slate-600">{item.effective_date}</td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${item.is_active ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'}`}>
                    {item.is_active ? 'Aktif' : 'Nonaktif'}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-amber-50 text-slate-500 hover:text-amber-600 transition-colors" title="Edit">
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

    if (terData.length === 0) {
      return (
        <div className="text-center py-12 text-sm text-slate-500">
          Belum ada bracket TER. Klik &quot;Tambah Bracket TER&quot; untuk menambahkan.
        </div>
      );
    }
    return (
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="text-left py-3 px-4 font-medium text-slate-600">Kategori</th>
            <th className="text-right py-3 px-4 font-medium text-slate-600">Min</th>
            <th className="text-right py-3 px-4 font-medium text-slate-600">Maks</th>
            <th className="text-right py-3 px-4 font-medium text-slate-600">Tarif (%)</th>
            <th className="text-left py-3 px-4 font-medium text-slate-600">Efektif</th>
            <th className="text-left py-3 px-4 font-medium text-slate-600">Status</th>
            <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {terData.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="py-3 px-4 text-slate-800 font-medium">{item.category}</td>
              <td className="py-3 px-4 text-right text-slate-600">{Number(item.income_range_min).toLocaleString('id-ID')}</td>
              <td className="py-3 px-4 text-right text-slate-600">{item.income_range_max ? Number(item.income_range_max).toLocaleString('id-ID') : '∞'}</td>
              <td className="py-3 px-4 text-right text-slate-600">{item.ter_rate}</td>
              <td className="py-3 px-4 text-slate-600">{item.effective_date}</td>
              <td className="py-3 px-4">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${item.is_active ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'}`}>
                  {item.is_active ? 'Aktif' : 'Nonaktif'}
                </span>
              </td>
              <td className="py-3 px-4">
                <div className="flex items-center justify-end gap-1">
                  <button onClick={() => openEditModal(item)} className="p-1.5 rounded-md hover:bg-amber-50 text-slate-500 hover:text-amber-600 transition-colors" title="Edit">
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
  };

  // ─── Render Form Fields ─────────────────────────────────────────────────────

  const renderFormFields = () => {
    if (activeTab === 'method') {
      return (
        <>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Metode Perhitungan PPh 21</label>
            <select
              value={methodForm.tax_calculation_method}
              onChange={(e) => setMethodForm({ ...methodForm, tax_calculation_method: e.target.value as 'PASAL_17' | 'TER' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            >
              <option value="PASAL_17">Pasal 17 (Progresif)</option>
              <option value="TER">TER (Tarif Efektif Rata-rata)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Metode Penggajian</label>
            <select
              value={methodForm.payroll_method}
              onChange={(e) => setMethodForm({ ...methodForm, payroll_method: e.target.value as MethodForm['payroll_method'] })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            >
              <option value="GROSS">Gross (Pajak ditanggung karyawan)</option>
              <option value="GROSS_UP">Gross Up (Tunjangan pajak agar nett sesuai target)</option>
              <option value="NETT">Nett (Pajak ditanggung perusahaan + tunjangan pajak)</option>
            </select>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={methodForm.is_active}
                onChange={(e) => setMethodForm({ ...methodForm, is_active: e.target.checked })}
                className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
              />
              Aktif
            </label>
          </div>
        </>
      );
    }

    if (activeTab === 'ptkp') {
      return (
        <>
          <FormField label="Kode PTKP" value={ptkpForm.ptkp_code} onChange={(v) => setPtkpForm({ ...ptkpForm, ptkp_code: v })} placeholder="Contoh: TK/0" />
          <FormField label="Deskripsi" value={ptkpForm.description} onChange={(v) => setPtkpForm({ ...ptkpForm, description: v })} placeholder="Contoh: Tidak Kawin, 0 Tanggungan" />
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Nominal Tahunan" value={ptkpForm.annual_amount} onChange={(v) => setPtkpForm({ ...ptkpForm, annual_amount: v })} placeholder="54000000" />
            <FormField label="Nominal Bulanan" value={ptkpForm.monthly_amount} onChange={(v) => setPtkpForm({ ...ptkpForm, monthly_amount: v })} placeholder="4500000" />
          </div>
          <FormField label="Referensi Regulasi" value={ptkpForm.regulation_reference} onChange={(v) => setPtkpForm({ ...ptkpForm, regulation_reference: v })} placeholder="Opsional" />
          <FormField label="Tahun Regulasi" value={ptkpForm.regulation_year} onChange={(v) => setPtkpForm({ ...ptkpForm, regulation_year: v })} placeholder="2024" />
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Tanggal Efektif" value={ptkpForm.effective_date} onChange={(v) => setPtkpForm({ ...ptkpForm, effective_date: v })} type="date" />
            <FormField label="Tanggal Berakhir (opsional)" value={ptkpForm.end_date} onChange={(v) => setPtkpForm({ ...ptkpForm, end_date: v })} type="date" />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={ptkpForm.is_active}
                onChange={(e) => setPtkpForm({ ...ptkpForm, is_active: e.target.checked })}
                className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
              />
              Aktif
            </label>
          </div>
        </>
      );
    }

    if (activeTab === 'brackets') {
      return (
        <>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Urutan Bracket" value={bracketForm.bracket_order} onChange={(v) => setBracketForm({ ...bracketForm, bracket_order: v })} placeholder="Contoh: 1" />
            <FormField label="Tarif Pajak (%)" value={bracketForm.tax_rate} onChange={(v) => setBracketForm({ ...bracketForm, tax_rate: v })} placeholder="Contoh: 0.05" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Rentang Penghasilan Min" value={bracketForm.income_range_min} onChange={(v) => setBracketForm({ ...bracketForm, income_range_min: v })} placeholder="0" />
            <FormField label="Rentang Penghasilan Maks (kosong = tak terbatas)" value={bracketForm.income_range_max} onChange={(v) => setBracketForm({ ...bracketForm, income_range_max: v })} placeholder="50000000" />
          </div>
          <FormField label="Tahun Regulasi" value={bracketForm.regulation_year} onChange={(v) => setBracketForm({ ...bracketForm, regulation_year: v })} placeholder="2024" />
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Tanggal Efektif" value={bracketForm.effective_date} onChange={(v) => setBracketForm({ ...bracketForm, effective_date: v })} type="date" />
            <FormField label="Tanggal Berakhir (opsional)" value={bracketForm.end_date} onChange={(v) => setBracketForm({ ...bracketForm, end_date: v })} type="date" />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={bracketForm.is_active}
                onChange={(e) => setBracketForm({ ...bracketForm, is_active: e.target.checked })}
                className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
              />
              Aktif
            </label>
          </div>
        </>
      );
    }

    return (
      <>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Kategori</label>
            <select
              value={terForm.category}
              onChange={(e) => setTerForm({ ...terForm, category: e.target.value as 'A' | 'B' | 'C' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            >
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
            </select>
          </div>
          <FormField label="Tarif Pajak (%)" value={terForm.ter_rate} onChange={(v) => setTerForm({ ...terForm, ter_rate: v })} placeholder="Contoh: 0.05" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <FormField label="Rentang Penghasilan Min" value={terForm.income_range_min} onChange={(v) => setTerForm({ ...terForm, income_range_min: v })} placeholder="0" />
          <FormField label="Rentang Penghasilan Maks (kosong = tak terbatas)" value={terForm.income_range_max} onChange={(v) => setTerForm({ ...terForm, income_range_max: v })} placeholder="50000000" />
        </div>
        <FormField label="Tahun Regulasi" value={terForm.regulation_year} onChange={(v) => setTerForm({ ...terForm, regulation_year: v })} placeholder="2024" />
        <div className="grid grid-cols-2 gap-4">
          <FormField label="Tanggal Efektif" value={terForm.effective_date} onChange={(v) => setTerForm({ ...terForm, effective_date: v })} type="date" />
          <FormField label="Tanggal Berakhir (opsional)" value={terForm.end_date} onChange={(v) => setTerForm({ ...terForm, end_date: v })} type="date" />
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={terForm.is_active}
              onChange={(e) => setTerForm({ ...terForm, is_active: e.target.checked })}
              className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
            />
            Aktif
          </label>
        </div>
      </>
    );
  };

  const getAddLabel = () => {
    if (activeTab === 'method') return 'Tambah Metode';
    if (activeTab === 'ptkp') return 'Tambah PTKP';
    if (activeTab === 'brackets') return 'Tambah Bracket';
    return 'Tambah Bracket TER';
  };

  const getModalTitle = () => {
    const action = editingItem ? 'Edit' : 'Tambah';
    if (activeTab === 'method') return `${action} Metode Pajak`;
    if (activeTab === 'ptkp') return `${action} PTKP`;
    if (activeTab === 'brackets') return `${action} Bracket Pasal 17`;
    return `${action} Bracket TER`;
  };

  const getDeleteName = () => {
    if (!deleteTarget) return '';
    if (activeTab === 'method') return deleteTarget.tax_calculation_method;
    if (activeTab === 'ptkp') return deleteTarget.ptkp_code;
    if (activeTab === 'brackets') return `Bracket ${deleteTarget.bracket_order}`;
    return `TER Kategori ${deleteTarget.category}`;
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
            className="border-b-2 border-amber-500 text-amber-600 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            PPh 21
          </Link>
        </nav>
      </div>

      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">PPh 21</h1>
        <p className="text-sm text-slate-500 mt-1">
          Konfigurasi metode pajak, PTKP, dan bracket Pasal 17 / TER
        </p>
      </div>

      {/* Entity Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-6">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`inline-flex items-center gap-2 whitespace-nowrap py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'border-amber-500 text-amber-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
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
          <h2 className="text-base font-semibold text-slate-800">{TABS.find((t) => t.key === activeTab)?.label}</h2>
          <button
            onClick={openAddModal}
            className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            {getAddLabel()}
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
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-800">
                {getModalTitle()}
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
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
              Apakah Anda yakin ingin menghapus <span className="font-semibold text-slate-800">{getDeleteName()}</span>?
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
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
        placeholder={placeholder}
      />
    </div>
  );
}
