'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Search, Download, Upload, FileDown, X } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { EmployeeListResponse } from '@/types';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card from '@/components/ui/Card';
import EmployeeTable from '@/components/employees/EmployeeTable';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const PAGE_SIZE = 20;

export default function EmployeesPage() {
  const router = useRouter();
  const [employees, setEmployees] = useState<EmployeeListResponse['items']>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [totalEmployees, setTotalEmployees] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);

  // Import modal state
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{ success: number; failed: number; errors?: string[] } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchEmployees = async (currentPage = page, currentSearch = search) => {
    setLoading(true);
    setError(null);
    try {
      const skip = currentPage * PAGE_SIZE;
      const searchParam = currentSearch ? `&search=${encodeURIComponent(currentSearch)}` : '';
      const data = await api.get<EmployeeListResponse>(
        `/api/v1/employees?company_id=1&skip=${skip}&limit=${PAGE_SIZE}${searchParam}`
      );
      setEmployees(data.items);
      setTotalEmployees(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Terjadi kesalahan saat memuat data');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees(0, search);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  useEffect(() => {
    fetchEmployees(page, search);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const paginatedEmployees = employees;

  const handleExport = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/excel/export/employees?company_id=1`);
      if (!res.ok) throw new Error('Export gagal');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'employees_export.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Gagal mengekspor data karyawan');
    }
  };

  const handleDownloadTemplate = () => {
    const headers = [
      'employee_code', 'first_name', 'last_name', 'gender', 'date_of_birth',
      'npwp', 'ptkp_status', 'phone', 'email', 'department_code',
      'position_code', 'grade_code', 'date_joined', 'bank_name',
      'bank_account_number', 'bank_account_name', 'bpjs_kes_number',
      'bpjs_tk_number', 'base_salary'
    ];
    const csvContent = headers.join(',') + '\n';
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'employee_import_template.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleImport = async () => {
    if (!importFile) return;
    setImporting(true);
    setImportResult(null);
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      formData.append('company_id', '1');
      const res = await fetch(`${API_BASE}/api/v1/excel/import/employees`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Import gagal');
      setImportResult({
        success: data.success_count ?? data.imported ?? 0,
        failed: data.failed_count ?? data.errors?.length ?? 0,
        errors: data.errors,
      });
      fetchEmployees();
    } catch (err: any) {
      setImportResult({ success: 0, failed: 1, errors: [err.message || 'Import gagal'] });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Data Karyawan</h1>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleDownloadTemplate}
            className="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <FileDown className="w-4 h-4 mr-1.5" />
            Download Template
          </button>
          <button
            type="button"
            onClick={() => { setShowImportModal(true); setImportFile(null); setImportResult(null); }}
            className="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-blue-300 text-blue-700 hover:bg-blue-50 transition-colors"
          >
            <Upload className="w-4 h-4 mr-1.5" />
            Import Excel
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-green-300 text-green-700 hover:bg-green-50 transition-colors"
          >
            <Download className="w-4 h-4 mr-1.5" />
            Export Excel
          </button>
          <Button onClick={() => router.push('/employees/new')}>
            <Plus className="w-4 h-4 mr-2" />
            Tambah Karyawan
          </Button>
        </div>
      </div>

      {/* Search */}
      <Card>
        <Input
          placeholder="Cari nama atau kode karyawan..."
          prefix={<Search className="w-4 h-4" />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Card>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Memuat data...</div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="secondary" onClick={() => fetchEmployees()}>
            Coba Lagi
          </Button>
        </div>
      ) : (
        <>
          <EmployeeTable
            employees={paginatedEmployees}
            onRowClick={(id) => router.push(`/employees/${id}`)}
          />

          {/* Pagination */}
          {totalEmployees > 0 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Menampilkan {page * PAGE_SIZE + 1}–
                {Math.min((page + 1) * PAGE_SIZE, totalEmployees)} dari{' '}
                {totalEmployees}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 relative">
            <button
              type="button"
              onClick={() => setShowImportModal(false)}
              className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Import Data Karyawan</h2>

            <div className="space-y-4">
              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-primary-400 transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                {importFile ? (
                  <p className="text-sm text-gray-700 font-medium">{importFile.name}</p>
                ) : (
                  <p className="text-sm text-gray-500">Klik untuk memilih file (.xlsx, .xls)</p>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  className="hidden"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                />
              </div>

              {importResult && (
                <div className={`rounded-lg p-3 text-sm ${
                  importResult.failed > 0 ? 'bg-yellow-50 text-yellow-800' : 'bg-green-50 text-green-800'
                }`}>
                  <p className="font-medium">
                    {importResult.success} berhasil diimport, {importResult.failed} gagal
                  </p>
                  {importResult.errors && importResult.errors.length > 0 && (
                    <ul className="mt-2 list-disc list-inside text-xs space-y-0.5">
                      {importResult.errors.slice(0, 5).map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                      {importResult.errors.length > 5 && (
                        <li>...dan {importResult.errors.length - 5} error lainnya</li>
                      )}
                    </ul>
                  )}
                </div>
              )}

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Tutup
                </button>
                <button
                  type="button"
                  onClick={handleImport}
                  disabled={!importFile || importing}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {importing ? 'Mengupload...' : 'Upload'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
