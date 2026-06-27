'use client';

import { useRef, useState } from 'react';
import { Download, Upload, FileSpreadsheet, Loader2 } from 'lucide-react';

interface ExcelActionsProps {
  module: 'bonuses' | 'thr' | 'reimbursements' | 'kasbon';
  companyId?: number;
  onImportSuccess?: () => void;
}

export function ExcelActions({ module, companyId = 1, onImportSuccess }: ExcelActionsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);

  const downloadFile = async (url: string, filename: string) => {
    const res = await fetch(url);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(data.detail?.message || data.message || `Gagal mengunduh ${filename}`);
      return;
    }
    const blob = await res.blob();
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(link.href);
  };

  const handleExport = () => {
    downloadFile(
      `/api/v1/excel/export/${module}?company_id=${companyId}`,
      `${module}_${companyId}.xlsx`
    );
  };

  const handleTemplate = () => {
    const url =
      module === 'thr' || module === 'kasbon'
        ? `/api/v1/excel/templates/${module}`
        : `/api/v1/excel/templates/${module}?company_id=${companyId}`;
    downloadFile(url, `${module}_template.xlsx`);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`/api/v1/excel/import/${module}?company_id=${companyId}`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const contentType = res.headers.get('content-type') || '';
        if (contentType.includes('spreadsheetml')) {
          const blob = await res.blob();
          const link = document.createElement('a');
          link.href = window.URL.createObjectURL(blob);
          link.download = `${module}_errors.xlsx`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(link.href);
          alert('Import sebagian gagal. File error telah diunduh.');
        } else {
          const data = await res.json().catch(() => ({}));
          alert(data.detail?.message || data.message || 'Import gagal');
        }
        return;
      }

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('spreadsheetml')) {
        const blob = await res.blob();
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = `${module}_errors.xlsx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(link.href);
        alert('Import sebagian gagal. File error telah diunduh.');
      } else {
        const data = await res.json();
        alert(`Import berhasil: ${data.success_count} baris, gagal: ${data.error_count}`);
        onImportSuccess?.();
      }
    } catch (err) {
      alert('Terjadi kesalahan saat import.');
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const labels: Record<string, string> = {
    bonuses: 'Bonus',
    thr: 'THR',
    reimbursements: 'Reimbursement',
    kasbon: 'Pinjaman',
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleExport}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        title={`Export ${labels[module]}`}
      >
        <Download className="w-4 h-4" />
        Export
      </button>
      <button
        onClick={handleTemplate}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        title={`Download Template ${labels[module]}`}
      >
        <FileSpreadsheet className="w-4 h-4" />
        Template
      </button>
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={importing}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        title={`Import ${labels[module]}`}
      >
        {importing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
        Import
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
