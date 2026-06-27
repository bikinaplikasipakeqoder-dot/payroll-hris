'use client';

import { useState, useEffect, useCallback } from 'react';
import { CheckCircle, XCircle, Download } from 'lucide-react';
import { api } from '@/lib/api';
import Button from '@/components/ui/Button';

interface JobStatus {
  job_id: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  total: number;
  completed: number;
  failed: number;
  message?: string;
  zip_url?: string;
}

interface ProgressModalProps {
  jobId: string | null;
  isActive: boolean;
  onComplete: () => void;
}

export default function ProgressModal({ jobId, isActive, onComplete }: ProgressModalProps) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollStatus = useCallback(async () => {
    if (!jobId) return;
    try {
      const data = await api.get<JobStatus>(`/api/v1/payslip/job-status/${jobId}`);
      setStatus(data);
      if (data.status === 'COMPLETED' || data.status === 'FAILED') {
        onComplete();
      }
    } catch {
      setError('Gagal mengambil status job');
    }
  }, [jobId, onComplete]);

  useEffect(() => {
    if (!isActive || !jobId) return;

    // Initial poll
    pollStatus();

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [isActive, jobId, pollStatus]);

  if (!isActive || !jobId) return null;

  const total = status?.total || 0;
  const completed = status?.completed || 0;
  const failed = status?.failed || 0;
  const percentage = total > 0 ? ((completed + failed) / total) * 100 : 0;
  const isCompleted = status?.status === 'COMPLETED';
  const isFailed = status?.status === 'FAILED';
  const isRunning = status?.status === 'IN_PROGRESS' || status?.status === 'PENDING';

  const handleDownloadZip = () => {
    if (status?.zip_url) {
      window.open(status.zip_url, '_blank');
    } else {
      window.open(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/payslip/bulk-download?job_id=${jobId}`,
        '_blank'
      );
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
      {/* Progress Bar */}
      {isRunning && (
        <>
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>Generating slip gaji {completed + failed}/{total}...</span>
            <span className="font-medium">{percentage.toFixed(1)}%</span>
          </div>
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full transition-all duration-300"
              style={{ width: `${percentage}%` }}
            />
          </div>
          {failed > 0 && (
            <p className="text-sm text-amber-600">{failed} gagal diproses</p>
          )}
        </>
      )}

      {/* Completed State */}
      {isCompleted && (
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <CheckCircle className="w-12 h-12 text-green-500" />
          </div>
          <p className="text-lg font-semibold text-gray-900">Generate Selesai!</p>
          <p className="text-sm text-gray-600">
            {completed} payslip berhasil digenerate, {failed} gagal
          </p>
          <Button size="lg" onClick={handleDownloadZip}>
            <Download className="w-4 h-4 mr-2" />
            Download ZIP
          </Button>
        </div>
      )}

      {/* Failed State */}
      {isFailed && (
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <XCircle className="w-12 h-12 text-red-500" />
          </div>
          <p className="text-lg font-semibold text-gray-900">Generate Gagal</p>
          <p className="text-sm text-red-600">
            {status?.message || 'Terjadi kesalahan saat memproses payslip'}
          </p>
          {completed > 0 && (
            <p className="text-sm text-gray-600">
              {completed} berhasil, {failed} gagal dari total {total}
            </p>
          )}
        </div>
      )}

      {/* Error polling state */}
      {error && (
        <p className="text-sm text-red-600 text-center">{error}</p>
      )}
    </div>
  );
}
