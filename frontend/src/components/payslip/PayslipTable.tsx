'use client';

import { useState, useMemo } from 'react';
import { Eye, Download, Printer, ArrowUpDown } from 'lucide-react';
import { PayslipRecord } from '@/types/payslip';
import { formatIDR, getMonthName } from '@/lib/utils';

interface PayslipTableProps {
  records: PayslipRecord[];
  onView: (record: PayslipRecord) => void;
  onDownload: (record: PayslipRecord) => void;
}

type SortKey = 'period' | 'gross_salary' | 'net_salary' | 'status';
type SortDir = 'asc' | 'desc';

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

export default function PayslipTable({ records, onView, onDownload }: PayslipTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('period');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sorted = useMemo(() => {
    const copy = [...records];
    copy.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'period':
          cmp = a.year * 100 + a.month - (b.year * 100 + b.month);
          break;
        case 'gross_salary':
          cmp = a.gross_salary - b.gross_salary;
          break;
        case 'net_salary':
          cmp = a.net_salary - b.net_salary;
          break;
        case 'status':
          cmp = a.status.localeCompare(b.status);
          break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return copy;
  }, [records, sortKey, sortDir]);

  const headerClass = 'px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:text-gray-700';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className={headerClass} onClick={() => toggleSort('period')}>
                <span className="inline-flex items-center gap-1">
                  Periode <ArrowUpDown className="w-3 h-3" />
                </span>
              </th>
              <th className={headerClass} onClick={() => toggleSort('gross_salary')}>
                <span className="inline-flex items-center gap-1">
                  Gaji Kotor <ArrowUpDown className="w-3 h-3" />
                </span>
              </th>
              <th className={headerClass}>Total Potongan</th>
              <th className={headerClass} onClick={() => toggleSort('net_salary')}>
                <span className="inline-flex items-center gap-1">
                  Gaji Bersih <ArrowUpDown className="w-3 h-3" />
                </span>
              </th>
              <th className={headerClass} onClick={() => toggleSort('status')}>
                <span className="inline-flex items-center gap-1">
                  Status <ArrowUpDown className="w-3 h-3" />
                </span>
              </th>
              <th className={`${headerClass} text-right`}>Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sorted.map((record) => (
              <tr key={record.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                  {getMonthName(record.month)} {record.year}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700 font-mono">
                  {formatIDR(record.gross_salary)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700 font-mono">
                  {formatIDR(record.gross_salary - record.net_salary)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 font-mono font-medium">
                  {formatIDR(record.net_salary)}
                </td>
                <td className="px-4 py-3">{getStatusBadge(record.status)}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => onView(record)}
                      className="p-1.5 rounded-md text-gray-500 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                      title="Lihat Detail"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onDownload(record)}
                      className="p-1.5 rounded-md text-gray-500 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                      title="Download PDF"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => window.print()}
                      className="p-1.5 rounded-md text-gray-500 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                      title="Print"
                    >
                      <Printer className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sorted.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Tidak ada data slip gaji
        </div>
      )}
    </div>
  );
}
