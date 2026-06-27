'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Shield,
  UserPlus,
  Pencil,
  CheckCircle,
  X,
  Users,
  Key,
  Info,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';

interface User {
  id: number;
  name: string;
  email: string;
  role: 'Administrator' | 'Payroll Master' | 'Operator' | 'Reporting';
  status: 'Aktif' | 'Nonaktif';
  lastLogin: string;
}

interface Role {
  name: string;
  description: string;
  color: string;
  bgColor: string;
  permissions: string[];
}

const MOCK_USERS: User[] = [
  { id: 1, name: 'Admin Utama', email: 'admin@company.com', role: 'Administrator', status: 'Aktif', lastLogin: 'Hari ini' },
  { id: 2, name: 'Budi Santoso', email: 'budi@company.com', role: 'Payroll Master', status: 'Aktif', lastLogin: '2 hari lalu' },
  { id: 3, name: 'Siti Rahayu', email: 'siti@company.com', role: 'Operator', status: 'Aktif', lastLogin: '1 jam lalu' },
  { id: 4, name: 'Andi Wijaya', email: 'andi@company.com', role: 'Reporting', status: 'Aktif', lastLogin: '5 hari lalu' },
];

const ROLES: Role[] = [
  {
    name: 'Administrator',
    description: 'Full access - semua modul, pengaturan sistem, manajemen pengguna',
    color: 'text-purple-700',
    bgColor: 'bg-purple-50 border-purple-200',
    permissions: [
      'Akses semua modul',
      'Pengaturan sistem',
      'Manajemen pengguna & peran',
      'Generate & approve payroll',
      'Export semua data',
    ],
  },
  {
    name: 'Payroll Master',
    description: 'Kelola payroll, generate slip gaji, approve lembur, laporan',
    color: 'text-blue-700',
    bgColor: 'bg-blue-50 border-blue-200',
    permissions: [
      'Kelola payroll',
      'Generate slip gaji',
      'Approve lembur',
      'Lihat & export laporan',
      'Kelola BPJS & pajak',
    ],
  },
  {
    name: 'Operator',
    description: 'Input data karyawan, kehadiran, kasbon, lihat data',
    color: 'text-green-700',
    bgColor: 'bg-green-50 border-green-200',
    permissions: [
      'Input data karyawan',
      'Kelola kehadiran',
      'Input kasbon & reimbursement',
      'Lihat data karyawan',
      'Input cuti & izin',
    ],
  },
  {
    name: 'Reporting',
    description: 'Lihat laporan, export data, tidak bisa edit',
    color: 'text-orange-700',
    bgColor: 'bg-orange-50 border-orange-200',
    permissions: [
      'Lihat semua laporan',
      'Export data ke Excel',
      'Lihat dashboard',
      'Akses read-only',
    ],
  },
];

const ROLE_BADGE_STYLES: Record<string, string> = {
  Administrator: 'bg-purple-100 text-purple-700',
  'Payroll Master': 'bg-blue-100 text-blue-700',
  Operator: 'bg-green-100 text-green-700',
  Reporting: 'bg-orange-100 text-orange-700',
};

export default function UsersSettingsPage() {
  const [users, setUsers] = useState<User[]>(MOCK_USERS);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: 'Operator' as User['role'],
    password: '',
    confirmPassword: '',
  });

  const handleToggleStatus = (id: number) => {
    setUsers((prev) =>
      prev.map((u) =>
        u.id === id
          ? { ...u, status: u.status === 'Aktif' ? 'Nonaktif' : 'Aktif' }
          : u
      )
    );
  };

  const handleAddUser = () => {
    if (!formData.name || !formData.email || !formData.password) return;
    if (formData.password !== formData.confirmPassword) return;

    const newUser: User = {
      id: Date.now(),
      name: formData.name,
      email: formData.email,
      role: formData.role,
      status: 'Aktif',
      lastLogin: 'Belum pernah',
    };
    setUsers((prev) => [...prev, newUser]);
    setFormData({ name: '', email: '', role: 'Operator', password: '', confirmPassword: '' });
    setShowModal(false);
  };

  return (
    <div>
      {/* Settings Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <Link
            href="/settings/ai"
            className="border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Pengaturan AI
          </Link>
          <Link
            href="/settings/users"
            className="border-b-2 border-indigo-500 text-indigo-600 whitespace-nowrap py-3 px-1 text-sm font-medium"
          >
            Manajemen Pengguna
          </Link>
        </nav>
      </div>

      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Manajemen Pengguna &amp; Peran</h1>
        <p className="text-sm text-slate-500 mt-1">
          Kelola akses pengguna sistem payroll
        </p>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700 mb-6 flex items-start gap-2">
        <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <span>
          Data pengguna saat ini menggunakan data demo. Integrasi backend akan ditambahkan.
        </span>
      </div>

      {/* Section 1: Daftar Pengguna */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-semibold text-slate-800">Daftar Pengguna</h2>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <UserPlus className="w-4 h-4" />
            Tambah Pengguna
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-slate-600">Nama</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Email</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Peran</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Status</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Terakhir Login</th>
                <th className="text-left py-3 px-4 font-medium text-slate-600">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium text-slate-800">{user.name}</td>
                  <td className="py-3 px-4 text-slate-600">{user.email}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${ROLE_BADGE_STYLES[user.role]}`}
                    >
                      {user.role}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        user.status === 'Aktif'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {user.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500">{user.lastLogin}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <button
                        className="p-1.5 rounded-md hover:bg-gray-100 text-slate-500 hover:text-slate-700 transition-colors"
                        title="Edit"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleToggleStatus(user.id)}
                        className="p-1.5 rounded-md hover:bg-gray-100 text-slate-500 hover:text-slate-700 transition-colors"
                        title={user.status === 'Aktif' ? 'Nonaktifkan' : 'Aktifkan'}
                      >
                        {user.status === 'Aktif' ? (
                          <ToggleRight className="w-4 h-4 text-green-600" />
                        ) : (
                          <ToggleLeft className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 2: Daftar Peran */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Key className="w-5 h-5 text-slate-600" />
          <h2 className="text-lg font-semibold text-slate-800">Daftar Peran</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ROLES.map((role) => (
            <div
              key={role.name}
              className={`rounded-lg border p-4 ${role.bgColor}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Shield className={`w-4 h-4 ${role.color}`} />
                  <h3 className={`font-semibold ${role.color}`}>{role.name}</h3>
                </div>
                <button className="text-xs text-slate-500 hover:text-slate-700 font-medium px-2 py-1 rounded hover:bg-white/60 transition-colors">
                  Edit Peran
                </button>
              </div>
              <p className="text-xs text-slate-600 mb-3">{role.description}</p>
              <ul className="space-y-1.5">
                {role.permissions.map((perm) => (
                  <li key={perm} className="flex items-center gap-2 text-xs text-slate-700">
                    <CheckCircle className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                    {perm}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Modal: Tambah Pengguna */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-xl border border-gray-200 p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-800">Tambah Pengguna</h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded-md hover:bg-gray-100 text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Nama Lengkap
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Masukkan nama lengkap"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="contoh@company.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Peran
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as User['role'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="Administrator">Administrator</option>
                  <option value="Payroll Master">Payroll Master</option>
                  <option value="Operator">Operator</option>
                  <option value="Reporting">Reporting</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Masukkan password"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Konfirmasi Password
                </label>
                <input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Ulangi password"
                />
              </div>

              {formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword && (
                <p className="text-xs text-red-500">Password tidak cocok</p>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm font-medium text-slate-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleAddUser}
                disabled={!formData.name || !formData.email || !formData.password || formData.password !== formData.confirmPassword}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Simpan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
