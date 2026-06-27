'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Gift, Loader2, AlertCircle, RefreshCw, Save } from 'lucide-react';
import { api, ApiError } from '@/lib/api';

interface THRConfig {
  id: number;
  company_id: number;
  payment_mode: 'BY_RELIGION' | 'UNIFIED';
  unified_holiday: string;
  full_tenure_months: number;
  min_tenure_months: number;
  prorate_partial_months: boolean;
  is_active: boolean;
}

const HOLIDAY_OPTIONS = [
  { value: 'IDUL_FITRI', label: 'Idul Fitri (Muslim)' },
  { value: 'CHRISTMAS', label: 'Natal (Kristen/Katolik)' },
  { value: 'NYEPI', label: 'Nyepi (Hindu)' },
  { value: 'WAISAK', label: 'Waisak (Buddha)' },
];

export default function THRSettingsPage() {
  const [config, setConfig] = useState<THRConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<THRConfig>('/api/v1/thr/config?company_id=1');
      setConfig(data);
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
    fetchConfig();
  }, [fetchConfig]);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setSaveError(null);
    setSuccess(false);
    try {
      await api.put('/api/v1/thr/config?company_id=1', {
        payment_mode: config.payment_mode,
        unified_holiday: config.unified_holiday,
        full_tenure_months: Number(config.full_tenure_months),
        min_tenure_months: Number(config.min_tenure_months),
        prorate_partial_months: config.prorate_partial_months,
        is_active: config.is_active,
      });
      setSuccess(true);
      fetchConfig();
    } catch (err) {
      if (err instanceof ApiError) {
        setSaveError(err.message);
      } else {
        setSaveError('Terjadi kesalahan saat menyimpan.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-pink-600" />
        <span className="ml-2 text-sm text-slate-500">Memuat konfigurasi THR...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
        <p className="text-sm text-slate-600 mb-3">{error}</p>
        <button
          onClick={fetchConfig}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-pink-600 border border-pink-300 rounded-lg hover:bg-pink-50 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Coba Lagi
        </button>
      </div>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <div className="max-w-3xl mx-auto">
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
            href="/settings/working-days"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Hari Kerja
          </Link>
          <Link
            href="/settings/thr"
            className="border-b-2 border-pink-500 text-pink-600 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            THR
          </Link>
        </nav>
      </div>

      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-pink-50">
            <Gift className="w-6 h-6 text-pink-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Pengaturan THR</h1>
            <p className="text-sm text-slate-500 mt-1">
              Atur mode pembayaran THR dan perhitungan prorate berdasarkan tanggal masuk karyawan
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        {/* Payment Mode */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Mode Pembayaran THR
          </label>
          <div className="space-y-3">
            <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
              <input
                type="radio"
                name="payment_mode"
                value="BY_RELIGION"
                checked={config.payment_mode === 'BY_RELIGION'}
                onChange={(e) => setConfig({ ...config, payment_mode: e.target.value as THRConfig['payment_mode'] })}
                className="mt-1 text-pink-600 focus:ring-pink-500"
              />
              <div>
                <p className="font-medium text-slate-800">Pisah per Agama</p>
                <p className="text-sm text-slate-500">
                  Setiap karyawan menerima THR sesuai hari raya keagamaannya masing-masing
                </p>
              </div>
            </label>
            <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
              <input
                type="radio"
                name="payment_mode"
                value="UNIFIED"
                checked={config.payment_mode === 'UNIFIED'}
                onChange={(e) => setConfig({ ...config, payment_mode: e.target.value as THRConfig['payment_mode'] })}
                className="mt-1 text-pink-600 focus:ring-pink-500"
              />
              <div>
                <p className="font-medium text-slate-800">Digabung / Serentak</p>
                <p className="text-sm text-slate-500">
                  Semua karyawan menerima THR bersamaan pada satu tanggal hari raya tertentu
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Unified Holiday */}
        {config.payment_mode === 'UNIFIED' && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Hari Raya untuk Pembayaran Bersama
            </label>
            <select
              value={config.unified_holiday}
              onChange={(e) => setConfig({ ...config, unified_holiday: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-pink-500"
            >
              {HOLIDAY_OPTIONS.map((h) => (
                <option key={h.value} value={h.value}>{h.label}</option>
              ))}
            </select>
            <p className="text-xs text-slate-500 mt-1">
              Contoh: jika dipilih Idul Fitri, maka semua karyawan akan diberikan THR saat Idul Fitri
            </p>
          </div>
        )}

        {/* Tenure thresholds */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Masa Kerja Penuh (bulan)
            </label>
            <input
              type="number"
              min={1}
              value={config.full_tenure_months}
              onChange={(e) => setConfig({ ...config, full_tenure_months: Number(e.target.value) })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-pink-500"
            />
            <p className="text-xs text-slate-500 mt-1">
              Default 12 bulan. THR dibayar penuh (1x gaji pokok) jika karyawan sudah bekerja minimal ini
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Masa Kerja Minimum (bulan)
            </label>
            <input
              type="number"
              min={0}
              value={config.min_tenure_months}
              onChange={(e) => setConfig({ ...config, min_tenure_months: Number(e.target.value) })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-pink-500"
            />
            <p className="text-xs text-slate-500 mt-1">
              Karyawan dengan masa kerja di bawah nilai ini tidak menerima THR
            </p>
          </div>
        </div>

        {/* Prorate partial months */}
        <div className="flex items-start gap-3">
          <input
            id="prorate_partial_months"
            type="checkbox"
            checked={config.prorate_partial_months}
            onChange={(e) => setConfig({ ...config, prorate_partial_months: e.target.checked })}
            className="mt-1 text-pink-600 focus:ring-pink-500 rounded"
          />
          <div>
            <label htmlFor="prorate_partial_months" className="block text-sm font-medium text-slate-700">
              Bulatkan ke Atas Bulan Parsial
            </label>
            <p className="text-xs text-slate-500">
              Jika aktif, masa kerja 5 bulan 10 hari akan dihitung sebagai 6 bulan
            </p>
          </div>
        </div>

        {/* Active */}
        <div className="flex items-start gap-3">
          <input
            id="is_active"
            type="checkbox"
            checked={config.is_active}
            onChange={(e) => setConfig({ ...config, is_active: e.target.checked })}
            className="mt-1 text-pink-600 focus:ring-pink-500 rounded"
          />
          <div>
            <label htmlFor="is_active" className="block text-sm font-medium text-slate-700">
              Konfigurasi Aktif
            </label>
            <p className="text-xs text-slate-500">
              Konfigurasi ini akan digunakan saat perhitungan THR otomatis
            </p>
          </div>
        </div>

        {saveError && (
          <div className="px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {saveError}
          </div>
        )}

        {success && (
          <div className="px-4 py-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm">
            Konfigurasi THR berhasil disimpan.
          </div>
        )}

        <div className="flex justify-end pt-4 border-t border-gray-100">
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2 bg-pink-600 text-white text-sm font-medium rounded-lg hover:bg-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Simpan Konfigurasi
          </button>
        </div>
      </div>
    </div>
  );
}
