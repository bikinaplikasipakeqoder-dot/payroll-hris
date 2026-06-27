import { api, ApiError } from './api';

export interface PayrollRun {
  id: number;
  company_id: number;
  payroll_period: string;
}

export interface BatchProgress {
  current: number;
  total: number;
  message: string;
}

export interface ProcessPayrollOptions {
  onProgress: (progress: BatchProgress) => void;
  onError: (message: string) => void;
  onComplete: () => void;
}

export async function processPayrollInBatches(
  run: PayrollRun,
  options: ProcessPayrollOptions
): Promise<void> {
  const { onProgress, onError, onComplete } = options;

  onProgress({ current: 0, total: 0, message: 'Mempersiapkan...' });

  try {
    const [year, month] = run.payroll_period.split('-').map(Number);
    const start = `${year}-${String(month).padStart(2, '0')}-01`;
    const end = new Date(year, month, 0).toISOString().split('T')[0];

    const ids = await api.get<number[]>(
      `/api/v1/payroll/preview/eligible-ids?company_id=${run.company_id}&period_start=${start}&period_end=${end}`
    );

    if (ids.length === 0) {
      onError('Tidak ada karyawan eligible untuk diproses.');
      return;
    }

    onProgress({ current: 0, total: ids.length, message: `Memproses 0/${ids.length} karyawan...` });

    const batchSize = 25;
    for (let i = 0; i < ids.length; i += batchSize) {
      const batch = ids.slice(i, i + batchSize);
      const isLast = i + batchSize >= ids.length;

      onProgress({
        current: i,
        total: ids.length,
        message: `Memproses ${i + 1}-${Math.min(i + batchSize, ids.length)} dari ${ids.length} karyawan...`,
      });

      await api.post(`/api/v1/payroll/runs/${run.id}/process-batch`, {
        employee_ids: batch,
        finalize: isLast,
      });

      onProgress({
        current: Math.min(i + batchSize, ids.length),
        total: ids.length,
        message: `Selesai ${Math.min(i + batchSize, ids.length)}/${ids.length} karyawan...`,
      });
    }

    onComplete();
  } catch (err) {
    const msg = err instanceof ApiError ? err.message : 'Gagal memproses payroll.';
    onError(msg);
  }
}
