'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  CalendarDays,
  Loader2,
  AlertCircle,
  RefreshCw,
  Save,
  Trash2,
  Briefcase,
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';

interface WorkingDaysConfig {
  id: number;
  company_id: number;
  year: number;
  month: number;
  working_days: number;
}

const MONTH_LABELS = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - 2 + i);

export default function WorkingDaysConfigPage() {
  const [year, setYear] = useState<number>(CURRENT_YEAR);
  const [configs, setConfigs] = useState<WorkingDaysConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<number | null>(null);

  const fetchConfigs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<WorkingDaysConfig[]>(
        `/api/v1/master-data/working-days?company_id=1&year=${year}`
      );
      setConfigs(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Gagal memuat data: ${err.message}`);
      } else {
        setError('Tidak dapat terhubung ke server.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, [year]);

  const getWorkingDays = (month: number): string => {
    const config = configs.find((c) => c.month === month);
    return config ? String(config.working_days) : '';
  };

  const getConfigId = (month: number): number | undefined => {
    const config = configs.find((c) => c.month === month);
    return config?.id;
  };

  const handleSave = async (month: number, value: string) => {
    const workingDays = value === '' ? 0 : Number(value);
    if (Number.isNaN(workingDays) || workingDays < 0 || workingDays > 31) {
      alert('Jumlah hari kerja harus antara 0 dan 31.');
      return;
    }

    setSaving(month);
    try {
      await api.post('/api/v1/master-data/working-days', {
        company_id: 1,
        year,
        month,
        working_days: workingDays,
      });
      await fetchConfigs();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menyimpan.');
    } finally {
      setSaving(null);
    }
  };

  const handleDelete = async (month: number) => {
    const id = getConfigId(month);
    if (!id) return;

    if (!confirm(`Hapus pengaturan hari kerja untuk ${MONTH_LABELS[month - 1]} ${year}?`)) {
      return;
    }

    try {
      await api.delete(`/api/v1/master-data/working-days/${id}`);
      await fetchConfigs();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menghapus.');
    }
  };

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
            href="/settings/working-days"
            className="border-b-2 border-blue-500 text-blue-600 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Hari Kerja
          </Link>
        </nav>
      </div>

      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Pengaturan Hari Kerja</h1>
        <p className="text-sm text-slate-500 mt-1">
          Atur jumlah hari kerja per bulan untuk perhitungan kehadiran dan gaji.
          Jika tidak diatur, sistem akan menghitung hari kerja berdasarkan hari Senin–Jumat.
        </p>
      </div>

      {/* Year Filter */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex items-center gap-3">
          <CalendarDays className="w-5 h-5 text-blue-600" />
          <label className="text-sm font-medium text-slate-700">Tahun</label>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {YEAR_OPTIONS.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Config Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            <span className="ml-2 text-sm text-slate-500">Memuat data...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
            <p className="text-sm text-slate-600 mb-3">{error}</p>
            <button
              onClick={fetchConfigs}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Coba Lagi
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Bulan</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Jumlah Hari Kerja</th>
                  <th className="text-left py-3 px-4 font-medium text-slate-600">Status</th>
                  <th className="text-right py-3 px-4 font-medium text-slate-600">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {MONTH_LABELS.map((label, index) => {
                  const month = index + 1;
                  const value = getWorkingDays(month);
                  const isConfigured = value !== '';
                  return (
                    <WorkingDaysRow
                      key={month}
                      month={month}
                      label={label}
                      initialValue={value}
                      isConfigured={isConfigured}
                      saving={saving === month}
                      onSave={handleSave}
                      onDelete={handleDelete}
                    />
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info Note */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
        <p>
          <strong>Catatan:</strong> Pengaturan ini digunakan oleh halaman Kehadiran untuk
          menghitung persentase kehadiran karyawan. Jika bulan tertentu belum diatur,
          sistem akan menggunakan jumlah hari Senin–Jumat di bulan tersebut.
        </p>
      </div>
    </div>
  );
}

function WorkingDaysRow({
  month,
  label,
  initialValue,
  isConfigured,
  saving,
  onSave,
  onDelete,
}: {
  month: number;
  label: string;
  initialValue: string;
  isConfigured: boolean;
  saving: boolean;
  onSave: (month: number, value: string) => void;
  onDelete: (month: number) => void;
}) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  return (
    <tr className="hover:bg-gray-50">
      <td className="py-3 px-4 text-slate-800 font-medium">{label}</td>
      <td className="py-3 px-4">
        <input
          type="number"
          min={0}
          max={31}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Kosong = default"
          className="w-32 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </td>
      <td className="py-3 px-4">
        {isConfigured ? (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
            Sudah diatur
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
            Default (Senin–Jumat)
          </span>
        )}
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={() => onSave(month, value)}
            disabled={saving}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Simpan
          </button>
          {isConfigured && (
            <button
              onClick={() => onDelete(month)}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Hapus
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
