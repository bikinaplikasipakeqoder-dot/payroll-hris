'use client';

import { Bell } from 'lucide-react';
import NotificationList from '@/components/notifications/NotificationList';

export default function NotificationsPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Bell className="w-6 h-6 text-gray-700" />
        <h1 className="text-2xl font-bold text-gray-900">Notifikasi</h1>
      </div>
      <NotificationList />
    </div>
  );
}
