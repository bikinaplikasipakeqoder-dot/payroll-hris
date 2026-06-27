'use client';

import { useState, useEffect } from 'react';
import { Download, FileText } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { AnnualSummaryResponse } from '@/types/payslip';
import { formatIDR, getMonthName } from '@/lib/utils';
import Button from '@/components/ui/Button';

const CURRENT_YEAR = new Date().getFullYear();
const EMPLOYEE_ID = 1; // Default for mock auth
const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - i);

export default function TaxSummaryPage() {
  const [year, setYear] = useState<number>(CURRENT_YEAR);
  const [data, setData] = useState<AnnualSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async (selectedYear: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<AnnualSummaryResponse>(
        `/api/v1/payslip/annual-summary/${EMPLOYEE_ID}/${selectedYear}`
      );
      setData(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Terjadi kesalahan saat memuat ringkasan pajak');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary(year);
  }, [year]);

  const handleDownloadPDF = () => {
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/payslip/annual-summary/${EMPLOYEE_ID}/${year}/pdf`;
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ringkasan Pajak Tahunan</h1>
          <p className="text-sm text-gray-500 mt-1">
            Preview 1721-A1 dan ringkasan penghasilan tahunan
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            {YEAR_OPTIONS.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="animate-pulse space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded-xl" />
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded-xl" />
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="secondary" onClick={() => fetchSummary(year)}>
            Coba Lagi
          </Button>
        </div>
      ) : !data ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Data tidak tersedia
          </h3>
          <p className="text-sm text-gray-500">
            Belum ada data penghasilan untuk tahun {year}.
          </p>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-sm text-gray-500 mb-1">Total Penghasilan Kotor</p>
              <p className="text-xl font-bold font-mono text-gray-900">
                {formatIDR(data.ytd_gross)}
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-sm text-gray-500 mb-1">Total PPh 21</p>
              <p className="text-xl font-bold font-mono text-red-600">
                {formatIDR(data.ytd_tax)}
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-sm text-gray-500 mb-1">Total BPJS</p>
              <p className="text-xl font-bold font-mono text-gray-900">
                {formatIDR(data.ytd_bpjs)}
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-sm text-gray-500 mb-1">Total Gaji Bersih</p>
              <p className="text-xl font-bold font-mono text-primary-600">
                {formatIDR(data.ytd_net)}
              </p>
            </div>
          </div>

          {/* Monthly Breakdown Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Rincian Bulanan</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Bulan
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Penghasilan Kotor
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      PPh 21
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      BPJS
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Gaji Bersih
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {Array.from({ length: 12 }, (_, i) => {
                    const monthNum = i + 1;
                    const monthData = data.months.find((m) => m.month === monthNum);
                    return (
                      <tr key={monthNum} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                          {getMonthName(monthNum)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 font-mono text-right">
                          {monthData ? formatIDR(monthData.gross_salary) : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 font-mono text-right">
                          {monthData ? formatIDR(monthData.pph21_tax) : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 font-mono text-right">
                          {monthData ? formatIDR(monthData.bpjs_total) : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 font-mono font-medium text-right">
                          {monthData ? formatIDR(monthData.net_salary) : '-'}
                        </td>
                      </tr>
                    );
                  })}
                  {/* Totals row */}
                  <tr className="bg-gray-50 font-bold">
                    <td className="px-4 py-3 text-sm text-gray-900">Total</td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-mono text-right">
                      {formatIDR(data.ytd_gross)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-mono text-right">
                      {formatIDR(data.ytd_tax)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-mono text-right">
                      {formatIDR(data.ytd_bpjs)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-mono text-right">
                      {formatIDR(data.ytd_net)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <Button onClick={handleDownloadPDF}>
              <Download className="w-4 h-4 mr-2" />
              Download Ringkasan PDF
            </Button>
            <Button variant="secondary">
              <Download className="w-4 h-4 mr-2" />
              Download Semua Slip Gaji (ZIP)
            </Button>
          </div>

          {/* Disclaimer */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
            <p className="text-sm text-yellow-800 italic">
              Ini adalah preview untuk referensi Anda. Form 1721-A1 resmi akan disediakan oleh HRD di bulan Januari.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
