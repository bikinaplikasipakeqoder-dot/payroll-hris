'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import {
  Clock,
  Calendar,
  Users,
  AlertTriangle,
  RefreshCw,
  Check,
  UserCheck,
  UserX,
  Thermometer,
  FileText,
  Download,
  Upload,
  X,
  Eye,
  Plus,
} from 'lucide-react';
import { api, ApiError, API_BASE } from '@/lib/api';
import Button from '@/components/ui/Button';
import { ExcelActions } from '@/components/ui/ExcelActions';
import { EmployeeSearchSelect } from '@/components/employees/EmployeeSearchSelect';

interface AttendanceRecord {
  id: number;
  employee_id: number;
  attendance_date: string;
  status: string;
  check_in_time: string | null;
  check_out_time: string | null;
  is_late: boolean;
  late_minutes: number;
  hours_worked: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

interface AttendanceSummary {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  total_working_days: number;
  present_days: number;
  absent_days: number;
  sick_days: number;
  leave_days: number;
  permitted_days: number;
  late_minutes: number;
  attendance_percentage: number;
}

interface OvertimeRecord {
  id: number;
  employee_id: number;
  overtime_date: string;
  overtime_type: string;
  hours: number;
  multiplier: number;
  calculated_amount: number | null;
  approval_status: string;
  approved_by: number | null;
  approval_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

interface Employee {
  id: number;
  employee_code: string;
  first_name: string;
  last_name: string | null;
}

type Tab = 'attendance' | 'overtime';

const ATTENDANCE_STATUS_BADGE: Record<string, string> = {
  PRESENT: 'bg-green-100 text-green-700',
  ABSENT: 'bg-red-100 text-red-700',
  SICK: 'bg-orange-100 text-orange-700',
  LEAVE: 'bg-blue-100 text-blue-700',
  PERMITTED: 'bg-purple-100 text-purple-700',
};

const APPROVAL_STATUS_BADGE: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
};

const CURRENT_YEAR = new Date().getFullYear();
const CURRENT_MONTH = new Date().getMonth() + 1;

const MONTH_OPTIONS = [
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

const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - 4 + i);

export default function AttendancePage() {
  const [activeTab, setActiveTab] = useState<Tab>('attendance');
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([]);
  const [summaries, setSummaries] = useState<AttendanceSummary[]>([]);
  const [overtimeRecords, setOvertimeRecords] = useState<OvertimeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [monthFilter, setMonthFilter] = useState<number>(CURRENT_MONTH);
  const [yearFilter, setYearFilter] = useState<number>(CURRENT_YEAR);
  const [approvingId, setApprovingId] = useState<number | null>(null);
  const [importing, setImporting] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<AttendanceSummary | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [showOvertimeModal, setShowOvertimeModal] = useState(false);
  const [submittingOvertime, setSubmittingOvertime] = useState(false);
  const [overtimeForm, setOvertimeForm] = useState({
    employee_id: '',
    overtime_date: '',
    overtime_type: 'WEEKDAY',
    hours: '',
    notes: '',
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchAttendanceSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<AttendanceSummary[]>(
        `/api/v1/attendance/summary?company_id=1&month=${monthFilter}&year=${yearFilter}`
      );
      setSummaries(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Tidak dapat memuat data. Pastikan server backend berjalan.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployeeDetail = async (employeeId: number) => {
    setDetailLoading(true);
    try {
      const startDate = `${yearFilter}-${String(monthFilter).padStart(2, '0')}-01`;
      const lastDay = new Date(yearFilter, monthFilter, 0).getDate();
      const endDate = `${yearFilter}-${String(monthFilter).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

      const data = await api.get<AttendanceRecord[]>(
        `/api/v1/attendance?employee_id=${employeeId}&date_from=${startDate}&date_to=${endDate}&skip=0&limit=1000`
      );
      setAttendanceRecords(data);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal memuat detail kehadiran.');
    } finally {
      setDetailLoading(false);
    }
  };

  const fetchOvertime = async () => {
    setLoading(true);
    setError(null);
    try {
      const startDate = `${yearFilter}-${String(monthFilter).padStart(2, '0')}-01`;
      const lastDay = new Date(yearFilter, monthFilter, 0).getDate();
      const endDate = `${yearFilter}-${String(monthFilter).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

      const data = await api.get<OvertimeRecord[]>(
        `/api/v1/attendance/overtime?company_id=1&date_from=${startDate}&date_to=${endDate}&skip=0&limit=1000`
      );
      setOvertimeRecords(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Tidak dapat memuat data. Pastikan server backend berjalan.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployees = async () => {
    try {
      const data = await api.get<Employee[]>('/api/v1/employees?company_id=1&skip=0&limit=1000');
      setEmployees(data);
    } catch (err) {
      console.error('Failed to load employees', err);
    }
  };

  useEffect(() => {
    if (activeTab === 'attendance') {
      fetchAttendanceSummary();
    } else {
      fetchOvertime();
    }
  }, [activeTab, monthFilter, yearFilter]);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const handleOpenDetail = (summary: AttendanceSummary) => {
    setSelectedEmployee(summary);
    fetchEmployeeDetail(summary.employee_id);
  };

  const handleCloseDetail = () => {
    setSelectedEmployee(null);
    setAttendanceRecords([]);
  };

  const handleApproveOvertime = async (overtimeId: number) => {
    setApprovingId(overtimeId);
    try {
      await api.patch(`/api/v1/attendance/overtime/${overtimeId}/approve`, {
        approval_status: 'APPROVED',
        approved_by: 1,
      });
      await fetchOvertime();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menyetujui lembur.');
    } finally {
      setApprovingId(null);
    }
  };

  const handleCreateOvertime = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!overtimeForm.employee_id || !overtimeForm.overtime_date || !overtimeForm.hours) {
      alert('Karyawan, tanggal, dan jam lembur wajib diisi.');
      return;
    }

    setSubmittingOvertime(true);
    try {
      await api.post('/api/v1/attendance/overtime', {
        employee_id: Number(overtimeForm.employee_id),
        overtime_date: overtimeForm.overtime_date,
        overtime_type: overtimeForm.overtime_type,
        hours: Number(overtimeForm.hours),
        notes: overtimeForm.notes || null,
      });
      setShowOvertimeModal(false);
      setOvertimeForm({
        employee_id: '',
        overtime_date: '',
        overtime_type: 'WEEKDAY',
        hours: '',
        notes: '',
      });
      await fetchOvertime();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal menambahkan lembur.');
    } finally {
      setSubmittingOvertime(false);
    }
  };

  const handleDownloadTemplate = () => {
    window.open(`${API_BASE}/api/v1/excel/templates/attendance`, '_blank');
  };

  const handleExport = () => {
    window.open(
      `${API_BASE}/api/v1/excel/export/attendance?company_id=1&month=${monthFilter}&year=${yearFilter}`,
      '_blank'
    );
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/api/v1/excel/import/attendance?company_id=1`, {
        method: 'POST',
        body: formData,
      });
      const contentType = res.headers.get('content-type') || '';

      if (!res.ok) {
        if (contentType.includes('application/json')) {
          const data = await res.json();
          throw new ApiError(
            res.status,
            data?.detail?.message || data?.detail || 'Import gagal',
            data
          );
        }
        throw new ApiError(res.status, 'Import gagal');
      }

      if (contentType.includes('application/json')) {
        const data = await res.json();
        alert(
          `Import selesai. Berhasil: ${data.success_count}/${data.total_rows} baris. Error: ${data.error_count}`
        );
        await fetchAttendanceSummary();
      } else {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'attendance_errors.xlsx';
        a.click();
        window.URL.revokeObjectURL(url);
        alert('Import selesai dengan error. File error telah diunduh.');
      }
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal mengimpor kehadiran.');
    } finally {
      setImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const summaryStats = useMemo(() => {
    const present = summaries.reduce((sum, s) => sum + s.present_days, 0);
    const absent = summaries.reduce((sum, s) => sum + s.absent_days, 0);
    const sick = summaries.reduce((sum, s) => sum + s.sick_days, 0);
    const leave = summaries.reduce((sum, s) => sum + s.leave_days + s.permitted_days, 0);
    return { present, absent, sick, leave };
  }, [summaries]);

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const formatTime = (time: string | null) => {
    if (!time) return '-';
    return time.substring(0, 5);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Kehadiran</h1>
        <p className="text-sm text-gray-500 mt-1">
          Monitoring kehadiran dan lembur karyawan
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('attendance')}
            className={`pb-3 px-1 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'attendance'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Clock className="w-4 h-4 inline-block mr-2" />
            Kehadiran Harian
          </button>
          <button
            onClick={() => setActiveTab('overtime')}
            className={`pb-3 px-1 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'overtime'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Calendar className="w-4 h-4 inline-block mr-2" />
            Lembur
          </button>
        </nav>
      </div>

      {/* Attendance Tab Content */}
      {activeTab === 'attendance' && (
        <>
          {/* Filters */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <select
                    value={monthFilter}
                    onChange={(e) => setMonthFilter(Number(e.target.value))}
                    className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    {MONTH_OPTIONS.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>

                <select
                  value={yearFilter}
                  onChange={(e) => setYearFilter(Number(e.target.value))}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {YEAR_OPTIONS.map((y) => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button variant="secondary" size="sm" onClick={handleDownloadTemplate}>
                  <Download className="w-4 h-4 mr-2" />
                  Template
                </Button>
                <Button variant="secondary" size="sm" onClick={handleExport}>
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
                <Button variant="primary" size="sm" onClick={handleImportClick} loading={importing}>
                  <Upload className="w-4 h-4 mr-2" />
                  Import
                </Button>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
            </div>
          </div>

          {/* Summary Cards */}
          {!loading && !error && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <UserCheck className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Hadir</p>
                    <p className="text-2xl font-bold text-gray-900">{summaryStats.present}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                    <UserX className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Absen</p>
                    <p className="text-2xl font-bold text-gray-900">{summaryStats.absent}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Thermometer className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Sakit</p>
                    <p className="text-2xl font-bold text-gray-900">{summaryStats.sick}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Izin</p>
                    <p className="text-2xl font-bold text-gray-900">{summaryStats.leave}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Attendance Summary Table */}
          {loading ? (
            <div className="text-center py-12 text-gray-500">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-gray-200 rounded w-1/4 mx-auto" />
                <div className="h-48 bg-gray-200 rounded" />
              </div>
            </div>
          ) : error ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
              <p className="text-gray-700 mb-4">{error}</p>
              <Button variant="secondary" onClick={fetchAttendanceSummary}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Coba Lagi
              </Button>
            </div>
          ) : summaries.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Belum ada data kehadiran
              </h3>
              <p className="text-sm text-gray-500">
                Data kehadiran untuk periode ini belum tersedia.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Kode Karyawan
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Nama Karyawan
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Hari Kerja
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Hadir
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Absen
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sakit
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Izin
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Telat (menit)
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        % Kehadiran
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Aksi
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {summaries.map((summary) => (
                      <tr
                        key={summary.employee_id}
                        className="hover:bg-gray-50 transition-colors cursor-pointer"
                        onClick={() => handleOpenDetail(summary)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                          {summary.employee_code}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {summary.employee_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                          {summary.total_working_days}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-green-700 text-center font-medium">
                          {summary.present_days}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-700 text-center font-medium">
                          {summary.absent_days}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-700 text-center font-medium">
                          {summary.sick_days}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-700 text-center font-medium">
                          {summary.leave_days + summary.permitted_days}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                          {summary.late_minutes || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center font-medium">
                          {summary.attendance_percentage}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenDetail(summary);
                            }}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            Detail
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Detail Modal */}
          {selectedEmployee && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
              <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Detail Kehadiran
                    </h3>
                    <p className="text-sm text-gray-500">
                      {selectedEmployee.employee_code} - {selectedEmployee.employee_name} | {MONTH_OPTIONS.find(m => m.value === monthFilter)?.label} {yearFilter}
                    </p>
                  </div>
                  <button
                    onClick={handleCloseDetail}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="p-6 overflow-auto flex-1">
                  {detailLoading ? (
                    <div className="text-center py-12 text-gray-500">
                      <div className="animate-pulse space-y-4">
                        <div className="h-4 bg-gray-200 rounded w-1/4 mx-auto" />
                        <div className="h-48 bg-gray-200 rounded" />
                      </div>
                    </div>
                  ) : attendanceRecords.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                      <p>Belum ada detail kehadiran untuk karyawan ini.</p>
                    </div>
                  ) : (
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Tanggal
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Jam Masuk
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Jam Keluar
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Jam Kerja
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Terlambat
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {attendanceRecords.map((record) => (
                          <tr key={record.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {formatDate(record.attendance_date)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${ATTENDANCE_STATUS_BADGE[record.status] || 'bg-gray-100 text-gray-700'}`}>
                                {record.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                              {formatTime(record.check_in_time)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                              {formatTime(record.check_out_time)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                              {record.hours_worked != null ? `${record.hours_worked} jam` : '-'}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                              {record.is_late ? (
                                <span className="text-red-600 font-medium">{record.late_minutes} menit</span>
                              ) : (
                                <span className="text-green-600">-</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                <div className="p-6 border-t border-gray-200 flex justify-end">
                  <Button variant="secondary" onClick={handleCloseDetail}>
                    Tutup
                  </Button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Overtime Tab Content */}
      {activeTab === 'overtime' && (
        <>
          {/* Overtime Toolbar */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <select
                    value={monthFilter}
                    onChange={(e) => setMonthFilter(Number(e.target.value))}
                    className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    {MONTH_OPTIONS.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>

                <select
                  value={yearFilter}
                  onChange={(e) => setYearFilter(Number(e.target.value))}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  {YEAR_OPTIONS.map((y) => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <ExcelActions
                  module="overtime"
                  companyId={1}
                  month={monthFilter}
                  year={yearFilter}
                  onImportSuccess={fetchOvertime}
                />
                <Button variant="primary" size="sm" onClick={() => setShowOvertimeModal(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Tambah Lembur
                </Button>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12 text-gray-500">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-gray-200 rounded w-1/4 mx-auto" />
                <div className="h-48 bg-gray-200 rounded" />
              </div>
            </div>
          ) : error ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
              <p className="text-gray-700 mb-4">{error}</p>
              <Button variant="secondary" onClick={fetchOvertime}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Coba Lagi
              </Button>
            </div>
          ) : overtimeRecords.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Belum ada data lembur
              </h3>
              <p className="text-sm text-gray-500">
                Data lembur karyawan akan muncul di sini.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tanggal
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Kode Karyawan
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tipe
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Jam
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status Approval
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Aksi
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {overtimeRecords.map((record) => (
                      <tr key={record.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(record.overtime_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                          EMP-{String(record.employee_id).padStart(4, '0')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            record.overtime_type === 'WEEKDAY'
                              ? 'bg-blue-100 text-blue-700'
                              : record.overtime_type === 'WEEKEND'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-orange-100 text-orange-700'
                          }`}>
                            {record.overtime_type === 'WEEKDAY'
                              ? 'Hari Kerja'
                              : record.overtime_type === 'WEEKEND'
                              ? 'Akhir Pekan'
                              : 'Hari Libur'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-mono">
                          {record.hours} jam
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${APPROVAL_STATUS_BADGE[record.approval_status] || 'bg-gray-100 text-gray-700'}`}>
                            {record.approval_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          {record.approval_status === 'PENDING' && (
                            <button
                              onClick={() => handleApproveOvertime(record.id)}
                              disabled={approvingId === record.id}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 rounded-lg transition-colors disabled:opacity-50"
                            >
                              <Check className="w-3.5 h-3.5" />
                              Setujui
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Add Overtime Modal */}
          {showOvertimeModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
              <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Tambah Lembur
                  </h3>
                  <button
                    onClick={() => setShowOvertimeModal(false)}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleCreateOvertime} className="p-6 space-y-4">
                  <EmployeeSearchSelect
                    employees={employees}
                    value={overtimeForm.employee_id}
                    onChange={(value) => setOvertimeForm({ ...overtimeForm, employee_id: value })}
                    label="Karyawan"
                  />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tanggal Lembur
                    </label>
                    <input
                      type="date"
                      required
                      value={overtimeForm.overtime_date}
                      onChange={(e) => setOvertimeForm({ ...overtimeForm, overtime_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipe Lembur
                    </label>
                    <select
                      value={overtimeForm.overtime_type}
                      onChange={(e) => setOvertimeForm({ ...overtimeForm, overtime_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="WEEKDAY">Hari Kerja</option>
                      <option value="WEEKEND">Akhir Pekan</option>
                      <option value="HOLIDAY">Hari Libur</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Jam Lembur
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="0.5"
                      required
                      value={overtimeForm.hours}
                      onChange={(e) => setOvertimeForm({ ...overtimeForm, hours: e.target.value })}
                      placeholder="Contoh: 3"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Keterangan
                    </label>
                    <textarea
                      value={overtimeForm.notes}
                      onChange={(e) => setOvertimeForm({ ...overtimeForm, notes: e.target.value })}
                      placeholder="Keterangan lembur (opsional)"
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-2">
                    <Button variant="secondary" type="button" onClick={() => setShowOvertimeModal(false)}>
                      Batal
                    </Button>
                    <Button variant="primary" type="submit" loading={submittingOvertime}>
                      Simpan
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
