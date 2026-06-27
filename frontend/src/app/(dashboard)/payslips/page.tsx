'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Download, FileText, Calendar } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { PayslipRecord } from '@/types/payslip';
import { formatIDR, getMonthName } from '@/lib/utils';
import PayslipCard from '@/components/payslip/PayslipCard';
import PayslipTable from '@/components/payslip/PayslipTable';
import Button from '@/components/ui/Button';

const CURRENT_YEAR = new Date().getFullYear();
const EMPLOYEE_ID = 1; // Default for mock auth

const YEAR_OPTIONS = Array.from({ length: 8 }, (_, i) => CURRENT_YEAR - 7 + i);
const MONTH_OPTIONS = [
  { value: 0, label: 'Semua' },
  { value: 1, label: 'Januari' },
  { value: 2, label: 'Februari' },
  { value: 3, label: 'Maret' },
  { value: 4, label: 'April' },
  { value: 5, label: 'Mei' },
  { value: 6, label: 'Juni' },
  { value: 7, label: 'Juli' },
  { value: 8, label: 'Agustus' },
  { value: 9, label: 'September' },
  { value: 10, label: 'Oktober' },
  { value: 11, label: 'November' },
  { value: 12, label: 'Desember' },
];

type QuickFilter = 'this_year' | 'last_12' | 'all';

export default function PayslipsPage() {
  const router = useRouter();
  const [records, setRecords] = useState<PayslipRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [yearFilter, setYearFilter] = useState<number>(CURRENT_YEAR);
  const [monthFilter, setMonthFilter] = useState<number>(0);
  const [quickFilter, setQuickFilter] = useState<QuickFilter>('this_year');

  const fetchPayslips = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<PayslipRecord[]>(
        `/api/v1/payslip/history?employee_id=${EMPLOYEE_ID}`
      );
      setRecords(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Terjadi kesalahan saat memuat data slip gaji');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayslips();
  }, []);

  const filteredRecords = useMemo(() => {
    let result = records;

    if (quickFilter === 'this_year') {
      result = result.filter((r) => r.year === CURRENT_YEAR);
    } else if (quickFilter === 'last_12') {
      const now = new Date();
      const cutoff = new Date(now.getFullYear(), now.getMonth() - 11, 1);
      result = result.filter((r) => {
        const recordDate = new Date(r.year, r.month - 1, 1);
        return recordDate >= cutoff;
      });
    }

    if (yearFilter && quickFilter === 'all') {
      result = result.filter((r) => r.year === yearFilter);
    }
    if (monthFilter > 0) {
      result = result.filter((r) => r.month === monthFilter);
    }

    return result;
  }, [records, yearFilter, monthFilter, quickFilter]);

  const recentPayslips = useMemo(() => {
    return [...records]
      .sort((a, b) => (b.year * 100 + b.month) - (a.year * 100 + a.month))
      .slice(0, 3);
  }, [records]);

  const handleQuickFilter = (filter: QuickFilter) => {
    setQuickFilter(filter);
    if (filter === 'this_year') {
      setYearFilter(CURRENT_YEAR);
      setMonthFilter(0);
    } else if (filter === 'last_12') {
      setMonthFilter(0);
    }
  };

  const handleView = (record: PayslipRecord) => {
    const period = `${record.year}-${String(record.month).padStart(2, '0')}`;
    router.push(`/payslips/${period}`);
  };

  const handleDownload = (record: PayslipRecord) => {
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/payslip/${EMPLOYEE_ID}/${record.year}/${record.month}`;
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Slip Gaji Saya</h1>
          <p className="text-sm text-gray-500 mt-1">
            Lihat dan unduh slip gaji Anda
          </p>
        </div>
        <Button onClick={() => handleDownload(records[0])} disabled={records.length === 0}>
          <Download className="w-4 h-4 mr-2" />
          Download All as ZIP
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Year dropdown */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-400" />
            <select
              value={yearFilter}
              onChange={(e) => {
                setYearFilter(Number(e.target.value));
                setQuickFilter('all');
              }}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {YEAR_OPTIONS.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          {/* Month dropdown */}
          <select
            value={monthFilter}
            onChange={(e) => setMonthFilter(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            {MONTH_OPTIONS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>

          {/* Quick filter buttons */}
          <div className="flex items-center gap-2 ml-auto">
            {([
              { key: 'this_year' as QuickFilter, label: 'Tahun Ini' },
              { key: 'last_12' as QuickFilter, label: '12 Bulan Terakhir' },
              { key: 'all' as QuickFilter, label: 'Semua' },
            ]).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => handleQuickFilter(key)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  quickFilter === key
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4 mx-auto" />
            <div className="h-32 bg-gray-200 rounded" />
          </div>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="secondary" onClick={fetchPayslips}>
            Coba Lagi
          </Button>
        </div>
      ) : records.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Belum ada slip gaji tersedia
          </h3>
          <p className="text-sm text-gray-500">
            Slip gaji Anda akan muncul di sini setelah diproses oleh HRD.
          </p>
        </div>
      ) : (
        <>
          {/* Recent Payslips */}
          {recentPayslips.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Slip Gaji Terbaru</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {recentPayslips.map((record) => (
                  <PayslipCard
                    key={record.id}
                    record={record}
                    onDownload={handleDownload}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Full History Table */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Riwayat Lengkap</h2>
            <PayslipTable
              records={filteredRecords}
              onView={handleView}
              onDownload={handleDownload}
            />
          </div>
        </>
      )}
    </div>
  );
}
