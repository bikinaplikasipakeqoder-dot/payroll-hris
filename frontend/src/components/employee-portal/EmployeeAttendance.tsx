'use client';

import { useState, useEffect, useCallback } from 'react';
import { Clock, LogIn, LogOut, Loader2, AlertCircle } from 'lucide-react';
import { api, ApiError } from '@/lib/api';

interface AttendanceRecord {
  id: number;
  attendance_date: string;
  status: string;
  check_in_time: string | null;
  check_out_time: string | null;
  is_late: boolean;
  late_minutes: number;
  hours_worked: string | null;
}

interface EmployeeAttendanceProps {
  employeeId: number;
}

export default function EmployeeAttendance({ employeeId }: EmployeeAttendanceProps) {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<'in' | 'out' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  const today = new Date().toISOString().split('T')[0];

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const dateFrom = new Date();
      dateFrom.setDate(dateFrom.getDate() - 30);
      const data = await api.get<AttendanceRecord[]>(
        `/api/v1/attendance?employee_id=${employeeId}&date_from=${dateFrom.toISOString().split('T')[0]}&date_to=${today}&limit=100`
      );
      setRecords(data);
      setTodayRecord(data.find((r) => r.attendance_date === today) || null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Tidak dapat memuat data kehadiran.');
      }
    } finally {
      setLoading(false);
    }
  }, [employeeId, today]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const handleClockIn = async () => {
    setActionLoading('in');
    try {
      await api.post(`/api/v1/attendance/clock-in?employee_id=${employeeId}`, {});
      fetchRecords();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal clock-in.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleClockOut = async () => {
    setActionLoading('out');
    try {
      await api.post(`/api/v1/attendance/clock-out?employee_id=${employeeId}`, {});
      fetchRecords();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Gagal clock-out.');
    } finally {
      setActionLoading(null);
    }
  };

  const formatTime = (time: string | null | undefined) => {
    if (!time) return '-';
    return time.substring(0, 5);
  };

  return (
    <div className="space-y-6">
      {/* Clock Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center">
              <Clock className="w-8 h-8 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Waktu Sekarang</p>
              <p className="text-3xl font-bold text-gray-900">
                {currentTime.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </p>
              <p className="text-sm text-gray-500">{new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right mr-4">
              <p className="text-xs text-gray-500">Masuk</p>
              <p className="text-lg font-semibold text-gray-900">{formatTime(todayRecord?.check_in_time)}</p>
            </div>
            <div className="text-right mr-4">
              <p className="text-xs text-gray-500">Pulang</p>
              <p className="text-lg font-semibold text-gray-900">{formatTime(todayRecord?.check_out_time)}</p>
            </div>

            {!todayRecord?.check_in_time ? (
              <button
                onClick={handleClockIn}
                disabled={actionLoading !== null}
                className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading === 'in' ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
                Clock In
              </button>
            ) : !todayRecord?.check_out_time ? (
              <button
                onClick={handleClockOut}
                disabled={actionLoading !== null}
                className="inline-flex items-center gap-2 px-6 py-3 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading === 'out' ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogOut className="w-4 h-4" />}
                Clock Out
              </button>
            ) : (
              <div className="px-6 py-3 bg-gray-100 text-gray-600 text-sm font-medium rounded-lg">
                Selesai
              </div>
            )}
          </div>
        </div>
      </div>

      {/* History */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">Riwayat Kehadiran (30 Hari Terakhir)</h3>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
            <p className="text-sm text-gray-600">{error}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Tanggal</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Masuk</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Pulang</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500">Terlambat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {records.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-gray-500">
                      Belum ada riwayat kehadiran.
                    </td>
                  </tr>
                ) : (
                  records.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-900">{record.attendance_date}</td>
                      <td className="py-3 px-4">
                        <StatusBadge status={record.status} />
                      </td>
                      <td className="py-3 px-4 text-gray-600">{formatTime(record.check_in_time)}</td>
                      <td className="py-3 px-4 text-gray-600">{formatTime(record.check_out_time)}</td>
                      <td className="py-3 px-4 text-right">
                        {record.is_late ? `${record.late_minutes} menit` : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    PRESENT: 'bg-emerald-100 text-emerald-700',
    ABSENT: 'bg-red-100 text-red-700',
    LEAVE: 'bg-blue-100 text-blue-700',
    SICK: 'bg-yellow-100 text-yellow-700',
    PERMITTED: 'bg-gray-100 text-gray-700',
  };
  const labels: Record<string, string> = {
    PRESENT: 'Hadir',
    ABSENT: 'Tidak Hadir',
    LEAVE: 'Cuti',
    SICK: 'Sakit',
    PERMITTED: 'Izin',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-700'}`}>
      {labels[status] || status}
    </span>
  );
}
