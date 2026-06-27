'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';
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

interface NotificationDropdownProps {
  onClose: () => void;
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
  return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
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

export default function NotificationDropdown({ onClose }: NotificationDropdownProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/notifications?employee_id=1&unread_only=false`
        );
        if (res.ok) {
          const data = await res.json();
          setNotifications(Array.isArray(data) ? data.slice(0, 5) : []);
        }
      } catch {
        // API not available - show empty state
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
    if (notification.link) {
      onClose();
    }
  };

  return (
    <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-900">Notifikasi</h3>
        <button
          onClick={markAllAsRead}
          className="text-xs text-primary-600 hover:text-primary-700 font-medium"
        >
          Tandai semua dibaca
        </button>
      </div>

      {/* Notification List */}
      <div className="max-h-80 overflow-y-auto">
        {loading ? (
          <div className="px-4 py-8 text-center">
            <div className="animate-spin w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full mx-auto" />
          </div>
        ) : notifications.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <p className="text-sm text-gray-500">Tidak ada notifikasi baru</p>
          </div>
        ) : (
          notifications.map((notification) => {
            const content = (
              <div
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                className={`px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 flex items-start gap-3 transition-colors ${
                  !notification.is_read ? 'bg-blue-50/50' : ''
                }`}
              >
                {getNotificationIcon(notification.type)}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${!notification.is_read ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'}`}>
                    {notification.title}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                    {notification.message}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {timeAgo(notification.created_at)}
                  </p>
                </div>
                {!notification.is_read && (
                  <span className="w-2 h-2 bg-primary-500 rounded-full flex-shrink-0 mt-2" />
                )}
              </div>
            );

            if (notification.link) {
              return (
                <Link key={notification.id} href={notification.link}>
                  {content}
                </Link>
              );
            }
            return content;
          })
        )}
      </div>

      {/* Footer */}
      <Link
        href="/notifications"
        onClick={onClose}
        className="block px-4 py-3 text-center text-sm font-medium text-primary-600 hover:bg-gray-50 border-t border-gray-100 transition-colors"
      >
        Lihat Semua Notifikasi
      </Link>
    </div>
  );
}
