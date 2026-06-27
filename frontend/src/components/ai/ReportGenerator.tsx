'use client';

import { useState } from 'react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { api, ApiError } from '@/lib/api';
import { AiReport } from './ReportResult';

interface ReportGeneratorProps {
  onGenerate: (report: AiReport, params: { report_type: string; period_month: number; period_year: number }) => void;
  isConfigured: boolean;
}

const REPORT_TYPES = [
  { value: 'payroll_summary', label: 'Ringkasan Payroll' },
  { value: 'overtime_analysis', label: 'Analisis Lembur' },
  { value: 'tax_compliance', label: 'Kepatuhan Pajak' },
  { value: 'employee_insights', label: 'Insight Karyawan' },
];

const MONTHS = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];

export default function ReportGenerator({ onGenerate, isConfigured }: ReportGeneratorProps) {
  const [reportType, setReportType] = useState('payroll_summary');
  const [periodMonth, setPeriodMonth] = useState(new Date().getMonth() + 1);
  const [periodYear, setPeriodYear] = useState(2026);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<AiReport>('/api/v1/ai/reports', {
        company_id: 1,
        report_type: reportType,
        period_month: periodMonth,
        period_year: periodYear,
      });
      onGenerate(response, { report_type: reportType, period_month: periodMonth, period_year: periodYear });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Terjadi kesalahan saat membuat laporan.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Generate Laporan AI</h3>

      {!isConfigured && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-800">
            AI belum dikonfigurasi. Silakan atur di{' '}
            <a href="/settings/ai" className="font-medium underline hover:text-amber-900">
              Pengaturan
            </a>
            .
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipe Laporan
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
            >
              {REPORT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Month */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bulan
            </label>
            <select
              value={periodMonth}
              onChange={(e) => setPeriodMonth(Number(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
            >
              {MONTHS.map((month, idx) => (
                <option key={idx + 1} value={idx + 1}>
                  {month}
                </option>
              ))}
            </select>
          </div>

          {/* Year */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tahun
            </label>
            <input
              type="number"
              value={periodYear}
              onChange={(e) => setPeriodYear(Number(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
            />
          </div>
        </div>

        <div className="mt-4">
          <Button
            type="submit"
            variant="primary"
            loading={isLoading}
            disabled={!isConfigured}
            className="w-full md:w-auto"
          >
            {isLoading ? 'Sedang membuat laporan...' : 'Generate Laporan'}
          </Button>
        </div>

        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}
      </form>
    </Card>
  );
}
