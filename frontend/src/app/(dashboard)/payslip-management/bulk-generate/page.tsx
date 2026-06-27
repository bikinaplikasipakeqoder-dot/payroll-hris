'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import ProgressModal from '@/components/payslip/ProgressModal';

interface BulkGenerateResponse {
  job_id: string;
  total_employees: number;
}

export default function BulkGeneratePage() {
  const router = useRouter();
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [employeeCount] = useState(200);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);
  const months = [
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

  const handleStartGenerate = async () => {
    setError(null);
    setLoading(true);
    try {
      const response = await api.post<BulkGenerateResponse>(
        '/api/v1/payslip/bulk-generate',
        { year, month, company_id: 1 }
      );
      setJobId(response.job_id);
      setIsGenerating(true);
      setIsPolling(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Gagal memulai proses generate');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    setIsPolling(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push('/payslip-management')}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Generate Slip Gaji Massal
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Generate slip gaji untuk seluruh karyawan sekaligus
          </p>
        </div>
      </div>

      {/* Form Card */}
      {!isGenerating && (
        <Card>
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-900">
              Pilih Periode Payroll
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-md">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tahun
                </label>
                <select
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  value={year}
                  onChange={(e) => setYear(Number(e.target.value))}
                >
                  {years.map((y) => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bulan
                </label>
                <select
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  value={month}
                  onChange={(e) => setMonth(Number(e.target.value))}
                >
                  {months.map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
              <p className="text-sm text-blue-800">
                <span className="font-medium">Jumlah Karyawan:</span> {employeeCount}
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <Button size="lg" onClick={handleStartGenerate} loading={loading}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Mulai Generate
            </Button>
          </div>
        </Card>
      )}

      {/* Progress Section */}
      {isGenerating && (
        <ProgressModal
          jobId={jobId}
          isActive={isPolling}
          onComplete={handleComplete}
        />
      )}

      {/* Show complete state actions */}
      {isGenerating && !isPolling && (
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={() => {
              setIsGenerating(false);
              setJobId(null);
            }}
          >
            Generate Ulang
          </Button>
          <Button
            variant="secondary"
            onClick={() => router.push('/payslip-management')}
          >
            Kembali ke Daftar
          </Button>
        </div>
      )}
    </div>
  );
}
