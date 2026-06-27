'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Download, Printer, AlertCircle } from 'lucide-react';
import { formatIDR, getMonthName } from '@/lib/utils';
import Button from '@/components/ui/Button';

const EMPLOYEE_ID = 1; // Default for mock auth
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PayslipDetail {
  employee_name: string;
  employee_code: string;
  bank_name: string | null;
  bank_account_number: string | null;
  gross_salary: number;
  net_salary: number;
  total_deductions: number;
  pph21_tax: number;
}

export default function PayslipDetailPage() {
  const params = useParams();
  const router = useRouter();
  const period = params.period as string; // "YYYY-MM"

  const [year, month] = period.split('-').map(Number);
  const periodLabel = `${getMonthName(month)} ${year}`;

  const [detail, setDetail] = useState<PayslipDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pdfUrl = `${API_BASE}/api/v1/payslip/${EMPLOYEE_ID}/${year}/${month}`;

  useEffect(() => {
    // For now, use mock detail since the endpoint returns a PDF
    // In production, there would be a separate detail JSON endpoint
    setLoading(true);
    const timer = setTimeout(() => {
      setDetail({
        employee_name: 'Karyawan',
        employee_code: 'EMP001',
        bank_name: 'BCA',
        bank_account_number: '1234567890',
        gross_salary: 15000000,
        net_salary: 12500000,
        total_deductions: 2500000,
        pph21_tax: 750000,
      });
      setLoading(false);
    }, 300);
    return () => clearTimeout(timer);
  }, [year, month]);

  const handleDownload = () => {
    window.open(pdfUrl, '_blank');
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
          <div className="h-48 bg-gray-200 rounded mb-4" />
          <div className="h-96 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <Button variant="secondary" onClick={() => router.back()}>
          Kembali
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => router.push('/payslips')}
        className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Kembali ke Daftar
      </button>

      {/* Summary Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Slip Gaji - {periodLabel}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {detail?.employee_name} ({detail?.employee_code})
            </p>
            {detail?.bank_name && (
              <p className="text-sm text-gray-500 mt-1">
                {detail.bank_name} - {detail.bank_account_number}
              </p>
            )}
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Gaji Bersih</p>
            <p className="text-3xl font-bold font-mono text-primary-600">
              {detail ? formatIDR(detail.net_salary) : '-'}
            </p>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500 mb-1">Penghasilan Kotor</p>
          <p className="text-xl font-bold font-mono text-gray-900">
            {detail ? formatIDR(detail.gross_salary) : '-'}
          </p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500 mb-1">Total Potongan</p>
          <p className="text-xl font-bold font-mono text-gray-900">
            {detail ? formatIDR(detail.total_deductions) : '-'}
          </p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500 mb-1">PPh 21</p>
          <p className="text-xl font-bold font-mono text-gray-900">
            {detail ? formatIDR(detail.pph21_tax) : '-'}
          </p>
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Preview Slip Gaji</h2>
        <iframe
          src={pdfUrl}
          className="w-full rounded-lg border border-gray-200"
          style={{ minHeight: '600px' }}
          title={`Payslip ${periodLabel}`}
        />
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <Button onClick={handleDownload}>
          <Download className="w-4 h-4 mr-2" />
          Download PDF
        </Button>
        <Button variant="secondary" onClick={handlePrint}>
          <Printer className="w-4 h-4 mr-2" />
          Print
        </Button>
        <Button variant="ghost">
          <AlertCircle className="w-4 h-4 mr-2" />
          Laporkan Masalah
        </Button>
      </div>
    </div>
  );
}
