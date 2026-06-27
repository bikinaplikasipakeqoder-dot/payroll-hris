'use client';

import Link from 'next/link';
import { Bot, Users, Database, Banknote, HeartPulse, Calculator, Wallet, Building2, MapPin, Cog, CalendarDays } from 'lucide-react';

const settingsLinks = [
  {
    title: 'Pengaturan AI',
    description: 'Konfigurasi provider AI untuk fitur chat dan laporan otomatis',
    href: '/settings/ai',
    icon: Bot,
    color: 'text-violet-600',
    bgColor: 'bg-violet-50',
  },
  {
    title: 'Manajemen Pengguna',
    description: 'Kelola akses pengguna dan peran dalam sistem payroll',
    href: '/settings/users',
    icon: Users,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
  },
  {
    title: 'Master Data',
    description: 'Kelola departemen, jabatan, grade, dan status kepegawaian',
    href: '/settings/master-data',
    icon: Database,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
  {
    title: 'Tunjangan',
    description: 'Kelola jenis tunjangan perusahaan dan aturan perhitungannya',
    href: '/settings/allowances',
    icon: Banknote,
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
  },
  {
    title: 'BPJS',
    description: 'Atur tarif iuran BPJS Kesehatan, JHT, JP, JKK, dan JKM',
    href: '/settings/bpjs',
    icon: HeartPulse,
    color: 'text-rose-600',
    bgColor: 'bg-rose-50',
  },
  {
    title: 'PPh 21',
    description: 'Konfigurasi metode pajak, PTKP, dan bracket Pasal 17 / TER',
    href: '/settings/tax',
    icon: Calculator,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
  },
  {
    title: 'Iuran',
    description: 'Kelola iuran karyawan seperti SPSI dan potongan lainnya',
    href: '/settings/iuran',
    icon: Wallet,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
  },
  {
    title: 'Entitas / Cabang',
    description: 'Kelola lokasi, entitas, dan cabang perusahaan',
    href: '/settings/entities',
    icon: Building2,
    color: 'text-cyan-600',
    bgColor: 'bg-cyan-50',
  },
  {
    title: 'UMP Regional',
    description: 'Atur Upah Minimum Provinsi/Kota berdasarkan lokasi',
    href: '/settings/ump',
    icon: MapPin,
    color: 'text-teal-600',
    bgColor: 'bg-teal-50',
  },
  {
    title: 'Rules Engine',
    description: 'Aturan kustom untuk perhitungan pajak, BPJS, lembur, dan tunjangan',
    href: '/settings/rules',
    icon: Cog,
    color: 'text-slate-600',
    bgColor: 'bg-slate-50',
  },
  {
    title: 'Hari Kerja',
    description: 'Atur jumlah hari kerja per bulan untuk perhitungan kehadiran',
    href: '/settings/working-days',
    icon: CalendarDays,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
];

export default function SettingsPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Pengaturan</h1>
        <p className="text-sm text-slate-500 mt-1">
          Kelola konfigurasi dan preferensi sistem
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {settingsLinks.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-gray-300 transition-all group"
          >
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-lg ${item.bgColor}`}>
                <item.icon className={`w-6 h-6 ${item.color}`} />
              </div>
              <div>
                <h2 className="font-semibold text-slate-800 group-hover:text-indigo-600 transition-colors">
                  {item.title}
                </h2>
                <p className="text-sm text-slate-500 mt-1">{item.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
