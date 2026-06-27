'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Download, RefreshCw, Eye, Search, FileText } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { PaginatedResponse } from '@/types';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card from '@/components/ui/Card';

// Inline types
interface PayslipRecord {
  id?: number;
  employee_id: number;
  employee_code: string;
  full_name: string;
  department: string;
  net_salary: number;
  status: 'generated' | 'pending';
  pdf_url?: string;
}

interface Employee {
  id: number;
  employee_code: string;
  full_name: string;
  department: string;
}

const DEPARTMENTS = ['All', 'Production', 'HR', 'Finance', 'IT', 'Sales'];
const PAGE_SIZE = 20;

const formatIDR = (amount: number) =>
  new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
  }).format(amount);

export default function PayslipManagementPage() {
  const router = useRouter();
  const [records, setRecords] = useState<PayslipRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('All');
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [page, setPage] = useState(0);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Try fetching payslip history, fallback to building from employees
      try {
        const data = await api.get<PayslipRecord[]>(
          `/api/v1/payslip/history?company_id=1&year=${year}&month=${month}`
        );
        setRecords(data);
      } catch {
        // Fallback: build list from employees
        const employees = await api.get<PaginatedResponse<Employee>>(
          `/api/v1/employees?company_id=1&skip=0&limit=300`
        );
        const mapped: PayslipRecord[] = employees.items.map((emp) => ({
          employee_id: emp.id,
          employee_code: emp.employee_code,
          full_name: emp.full_name,
          department: emp.department || 'Unknown',
          net_salary: 0,
          status: 'pending' as const,
        }));
        setRecords(mapped);
      }
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
    fetchData();
  }, [year, month]);

  const filteredRecords = useMemo(() => {
    let result = records;
    if (department !== 'All') {
      result = result.filter(
        (r) => r.department.toLowerCase() === department.toLowerCase()
      );
    }
    if (search.trim()) {
      const query = search.toLowerCase();
      result = result.filter(
        (r) =>
          r.full_name.toLowerCase().includes(query) ||
          r.employee_code.toLowerCase().includes(query)
      );
    }
    return result;
  }, [records, department, search]);

  const totalFiltered = filteredRecords.length;
  const paginatedRecords = filteredRecords.slice(
    page * PAGE_SIZE,
    (page + 1) * PAGE_SIZE
  );
  const totalPages = Math.ceil(totalFiltered / PAGE_SIZE);

  useEffect(() => {
    setPage(0);
  }, [search, department]);

  const handleDownloadAll = () => {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/payslip/bulk-download?year=${year}&month=${month}`,
      '_blank'
    );
  };

  const handleViewPdf = (record: PayslipRecord) => {
    if (record.pdf_url) {
      window.open(record.pdf_url, '_blank');
    } else {
      window.open(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/payslip/download/${record.employee_id}?year=${year}&month=${month}`,
        '_blank'
      );
    }
  };

  const handleDownloadSingle = (record: PayslipRecord) => {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/payslip/download/${record.employee_id}?year=${year}&month=${month}`,
      '_blank'
    );
  };

  const handleGenerateSingle = async (record: PayslipRecord) => {
    try {
      await api.post('/api/v1/payslip/generate', {
        employee_id: record.employee_id,
        year,
        month,
      });
      fetchData();
    } catch {
      // Silent fail — could add toast here
    }
  };

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Kelola Slip Gaji</h1>
          <p className="text-sm text-gray-500 mt-1">
            Generate dan kelola slip gaji karyawan
          </p>
        </div>
        <div className="flex gap-3">
          <Button onClick={() => router.push('/payslip-management/bulk-generate')}>
            <FileText className="w-4 h-4 mr-2" />
            Generate Semua Payslip
          </Button>
          <Button variant="secondary" onClick={handleDownloadAll}>
            <Download className="w-4 h-4 mr-2" />
            Download Semua (ZIP)
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Departemen
            </label>
            <select
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            >
              {DEPARTMENTS.map((d) => (
                <option key={d} value={d}>{d === 'All' ? 'Semua Departemen' : d}</option>
              ))}
            </select>
          </div>
          <div>
            <Input
              label="Cari Karyawan"
              placeholder="Nama atau kode..."
              prefix={<Search className="w-4 h-4" />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </Card>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Memuat data...</div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="secondary" onClick={fetchData}>
            Coba Lagi
          </Button>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">
                      Kode Karyawan
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">
                      Nama
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">
                      Departemen
                    </th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">
                      Gaji Bersih (IDR)
                    </th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">
                      Status Payslip
                    </th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">
                      Aksi
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {paginatedRecords.map((record, idx) => (
                    <tr key={`${record.employee_code}-${idx}`} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-gray-800">
                        {record.employee_code}
                      </td>
                      <td className="px-4 py-3 text-gray-900">{record.full_name}</td>
                      <td className="px-4 py-3 text-gray-600">{record.department}</td>
                      <td className="px-4 py-3 text-right text-gray-900">
                        {record.net_salary > 0 ? formatIDR(record.net_salary) : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {record.status === 'generated' ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Generated
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                            Belum Digenerate
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                            title="Lihat PDF"
                            onClick={() => handleViewPdf(record)}
                            disabled={record.status !== 'generated'}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                            title="Download"
                            onClick={() => handleDownloadSingle(record)}
                            disabled={record.status !== 'generated'}
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          <button
                            className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                            title="Generate"
                            onClick={() => handleGenerateSingle(record)}
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {paginatedRecords.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                        Tidak ada data ditemukan
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalFiltered > 0 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Menampilkan {page * PAGE_SIZE + 1}–
                {Math.min((page + 1) * PAGE_SIZE, totalFiltered)} dari {totalFiltered}
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
    </div>
  );
}
