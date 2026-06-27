'use client';

import { Download } from 'lucide-react';
import { PayslipRecord } from '@/types/payslip';
import { formatIDR, getMonthName } from '@/lib/utils';

interface PayslipCardProps {
  record: PayslipRecord;
  onDownload?: (record: PayslipRecord) => void;
}

function getStatusBadge(status: string) {
  const lower = status.toLowerCase();
  if (lower === 'generated' || lower === 'completed') {
    return (
      <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
        Generated
      </span>
    );
  }
  if (lower === 'pending' || lower === 'processing') {
    return (
      <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
        Pending
      </span>
    );
  }
  return (
    <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
      Failed
    </span>
  );
}

export default function PayslipCard({ record, onDownload }: PayslipCardProps) {
  const periodLabel = `${getMonthName(record.month)} ${record.year}`;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-center justify-between hover:shadow-md transition-shadow">
      <div className="flex-1">
        <p className="text-sm text-gray-500 mb-1">{periodLabel}</p>
        <p className="text-xl font-bold font-mono text-gray-900">
          {formatIDR(record.net_salary)}
        </p>
        <div className="mt-2">{getStatusBadge(record.status)}</div>
      </div>
      <button
        onClick={() => onDownload?.(record)}
        className="ml-4 p-2 rounded-lg text-gray-500 hover:text-primary-600 hover:bg-primary-50 transition-colors"
        title="Download PDF"
      >
        <Download className="w-5 h-5" />
      </button>
    </div>
  );
}
