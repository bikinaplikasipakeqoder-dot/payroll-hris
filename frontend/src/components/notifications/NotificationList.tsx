'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle, Bell } from 'lucide-react';
import Link from 'next/link';

interface Notification {
  id: number;
  employee_id: number;
  type: string;
  title: string;
  message: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffMin < 1) return 'Baru saja';
  if (diffMin < 60) return `${diffMin} menit lalu`;
  if (diffHour < 24) return `${diffHour} jam lalu`;
  if (diffDay < 7) return `${diffDay} hari lalu`;
  return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
}

function getNotificationIcon(type: string) {
  switch (type) {
    case 'PAYSLIP_READY':
    case 'BULK_COMPLETE':
      return <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />;
    case 'BULK_FAILED':
      return <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />;
    default:
      return <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0" />;
  }
}

export default function NotificationList() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/notifications?employee_id=1`
        );
        if (res.ok) {
          const data = await res.json();
          setNotifications(Array.isArray(data) ? data : []);
        }
      } catch {
        // API not available
      } finally {
        setLoading(false);
      }
    };
    fetchNotifications();
  }, []);

  const markAsRead = async (id: number) => {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/notifications/${id}/read`,
        { method: 'PATCH', headers: { 'Content-Type': 'application/json' } }
      );
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {}
  };

  const markAllAsRead = async () => {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/notifications/mark-all-read?employee_id=1`,
        { method: 'PATCH', headers: { 'Content-Type': 'application/json' } }
      );
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin w-6 h-6 border-2 border-gray-300 border-t-primary-500 rounded-full" />
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">Tidak ada notifikasi</h3>
        <p className="text-sm text-gray-500">Belum ada notifikasi untuk ditampilkan.</p>
      </div>
    );
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="space-y-4">
      {/* Header actions */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          {unreadCount > 0 ? `${unreadCount} belum dibaca` : 'Semua sudah dibaca'}
        </p>
        {unreadCount > 0 && (
          <button
            onClick={markAllAsRead}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Tandai semua dibaca
          </button>
        )}
      </div>

      {/* Notification items */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden divide-y divide-gray-100">
        {notifications.map((notification) => {
          const inner = (
            <div
              key={notification.id}
              onClick={() => handleNotificationClick(notification)}
              className={`px-5 py-4 flex items-start gap-4 cursor-pointer transition-colors hover:bg-gray-50 ${
                !notification.is_read ? 'bg-blue-50/40 border-l-[3px] border-l-primary-500' : 'border-l-[3px] border-l-transparent'
              }`}
            >
              {getNotificationIcon(notification.type)}
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${!notification.is_read ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'}`}>
                  {notification.title}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {notification.message}
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  {timeAgo(notification.created_at)}
                </p>
              </div>
              {!notification.is_read && (
                <span className="w-2.5 h-2.5 bg-primary-500 rounded-full flex-shrink-0 mt-1.5" />
              )}
            </div>
          );

          if (notification.link) {
            return (
              <Link key={notification.id} href={notification.link} className="block">
                {inner}
              </Link>
            );
          }
          return <div key={notification.id}>{inner}</div>;
        })}
      </div>
    </div>
  );
}
