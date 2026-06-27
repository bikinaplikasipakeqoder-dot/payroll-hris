'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { employeeFormSchema, EmployeeFormData } from './EmployeeFormSchema';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import EmployeeAllowances from './EmployeeAllowances';

interface MasterOption {
  id: number;
  name?: string;
  grade_code?: string;
  grade_name?: string;
}

interface EmployeeFormProps {
  mode: 'create' | 'edit';
  employeeId?: number;
  defaultValues?: Partial<EmployeeFormData>;
  onSubmit: (data: EmployeeFormData) => Promise<void>;
  isSubmitting: boolean;
}

const tabs = [
  { id: 'personal', label: 'Data Pribadi' },
  { id: 'employment', label: 'Kepegawaian' },
  { id: 'salary', label: 'Gaji & Pajak' },
  { id: 'allowances', label: 'Tunjangan' },
  { id: 'bpjs', label: 'BPJS & Bank' },
  { id: 'address', label: 'Alamat' },
] as const;

type TabId = (typeof tabs)[number]['id'];

const PTKP_OPTIONS = ['TK/0', 'TK/1', 'TK/2', 'TK/3', 'K/0', 'K/1', 'K/2', 'K/3'] as const;
const RELIGION_OPTIONS = ['Islam', 'Protestan', 'Katolik', 'Hindu', 'Buddha', 'Konghucu'] as const;

export default function EmployeeForm({ mode, employeeId, defaultValues, onSubmit, isSubmitting }: EmployeeFormProps) {
  const [activeTab, setActiveTab] = useState<TabId>('personal');
  const router = useRouter();

  // Master data states
  const [departments, setDepartments] = useState<MasterOption[]>([]);
  const [positions, setPositions] = useState<MasterOption[]>([]);
  const [grades, setGrades] = useState<MasterOption[]>([]);
  const [employmentStatuses, setEmploymentStatuses] = useState<MasterOption[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [masterLoading, setMasterLoading] = useState(true);
  const [masterError, setMasterError] = useState(false);

  useEffect(() => {
    const fetchMasterData = async () => {
      setMasterLoading(true);
      try {
        const [depts, pos, grd, statuses, ents] = await Promise.all([
          api.get<MasterOption[]>('/api/v1/master-data/departments?company_id=1').catch(() => []),
          api.get<MasterOption[]>('/api/v1/master-data/positions?company_id=1').catch(() => []),
          api.get<MasterOption[]>('/api/v1/master-data/grades?company_id=1').catch(() => []),
          api.get<MasterOption[]>('/api/v1/master-data/employment-statuses?company_id=1').catch(() => []),
          api.get<Entity[]>('/api/v1/companies/1/entities').catch(() => []),
        ]);
        setDepartments(depts);
        setPositions(pos);
        setGrades(grd);
        setEmploymentStatuses(statuses);
        setEntities(ents);
        if (!depts.length && !pos.length && !grd.length && !statuses.length) {
          setMasterError(true);
        }
      } catch {
        setMasterError(true);
      } finally {
        setMasterLoading(false);
      }
    };
    fetchMasterData();
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EmployeeFormData>({
    resolver: zodResolver(employeeFormSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      gender: null,
      date_of_birth: '',
      personal_id_number: '',
      phone: '',
      email: '',
      employee_code: '',
      date_joined: '',
      department_id: null,
      position_id: null,
      grade_id: null,
      employment_status_id: null,
      entity_id: null,
      ptkp_status: 'TK/0',
      religion: 'Islam',
      base_salary: null,
      base_salary_effective_date: '',
      npwp_number: '',
      bpjs_kes_number: '',
      bpjs_tk_number: '',
      bank_name: '',
      bank_account_number: '',
      bank_account_name: '',
      address_street: '',
      address_city: '',
      address_province: '',
      address_postal_code: '',
      ...defaultValues,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap py-3 px-1 border-b-2 text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600 font-medium'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="pt-2">
        {/* Tab 1: Data Pribadi */}
        {activeTab === 'personal' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Nama Depan *"
              {...register('first_name')}
              error={errors.first_name?.message}
              placeholder="Masukkan nama depan"
            />
            <Input
              label="Nama Belakang"
              {...register('last_name')}
              error={errors.last_name?.message}
              placeholder="Masukkan nama belakang"
            />
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Jenis Kelamin
              </label>
              <select
                {...register('gender')}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Pilih jenis kelamin</option>
                <option value="M">Laki-laki</option>
                <option value="F">Perempuan</option>
              </select>
              {errors.gender && (
                <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>
              )}
            </div>
            <Input
              label="Tanggal Lahir"
              type="date"
              {...register('date_of_birth')}
              error={errors.date_of_birth?.message}
            />
            <Input
              label="No. KTP"
              {...register('personal_id_number')}
              error={errors.personal_id_number?.message}
              placeholder="Masukkan No. KTP"
            />
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Agama
              </label>
              <select
                {...register('religion')}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {RELIGION_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
              {errors.religion && (
                <p className="mt-1 text-sm text-red-600">{errors.religion.message}</p>
              )}
            </div>
            <Input
              label="No. Telepon"
              {...register('phone')}
              error={errors.phone?.message}
              placeholder="08xxxxxxxxxx"
            />
            <Input
              label="Email"
              type="email"
              {...register('email')}
              error={errors.email?.message}
              placeholder="email@contoh.com"
            />
          </div>
        )}

        {/* Tab 2: Kepegawaian */}
        {activeTab === 'employment' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Kode Karyawan *"
              {...register('employee_code')}
              error={errors.employee_code?.message}
              placeholder="EMP-001"
            />
            <Input
              label="Tanggal Bergabung *"
              type="date"
              {...register('date_joined')}
              error={errors.date_joined?.message}
            />
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Departemen</label>
              <select
                {...register('department_id', { valueAsNumber: true })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={masterLoading}
              >
                <option value="">{masterLoading ? 'Memuat...' : departments.length ? 'Pilih Departemen' : 'Data tidak tersedia'}</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
              {errors.department_id && (
                <p className="mt-1 text-sm text-red-600">{errors.department_id.message}</p>
              )}
            </div>
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Jabatan</label>
              <select
                {...register('position_id', { valueAsNumber: true })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={masterLoading}
              >
                <option value="">{masterLoading ? 'Memuat...' : positions.length ? 'Pilih Jabatan' : 'Data tidak tersedia'}</option>
                {positions.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              {errors.position_id && (
                <p className="mt-1 text-sm text-red-600">{errors.position_id.message}</p>
              )}
            </div>
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Grade</label>
              <select
                {...register('grade_id', { valueAsNumber: true })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={masterLoading}
              >
                <option value="">{masterLoading ? 'Memuat...' : grades.length ? 'Pilih Grade' : 'Data tidak tersedia'}</option>
                {grades.map((g) => (
                  <option key={g.id} value={g.id}>{g.grade_code && g.grade_name ? `${g.grade_code} - ${g.grade_name}` : g.name}</option>
                ))}
              </select>
              {errors.grade_id && (
                <p className="mt-1 text-sm text-red-600">{errors.grade_id.message}</p>
              )}
            </div>
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Status Kepegawaian</label>
              <select
                {...register('employment_status_id', { valueAsNumber: true })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={masterLoading}
              >
                <option value="">{masterLoading ? 'Memuat...' : employmentStatuses.length ? 'Pilih Status Kepegawaian' : 'Data tidak tersedia'}</option>
                {employmentStatuses.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
              {errors.employment_status_id && (
                <p className="mt-1 text-sm text-red-600">{errors.employment_status_id.message}</p>
              )}
            </div>
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status PTKP
              </label>
              <select
                {...register('ptkp_status')}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {PTKP_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
              {errors.ptkp_status && (
                <p className="mt-1 text-sm text-red-600">{errors.ptkp_status.message}</p>
              )}
            </div>
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Entitas / Lokasi</label>
              <select
                {...register('entity_id', { valueAsNumber: true })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={masterLoading}
              >
                <option value="">{masterLoading ? 'Memuat...' : entities.length ? 'Pilih Entitas' : 'Data tidak tersedia'}</option>
                {entities.map((e) => (
                  <option key={e.id} value={e.id}>{e.code} - {e.name} {e.city ? `(${e.city})` : ''}</option>
                ))}
              </select>
              {errors.entity_id && (
                <p className="mt-1 text-sm text-red-600">{errors.entity_id.message}</p>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Gaji & Pajak */}
        {activeTab === 'salary' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Gaji Pokok"
              type="number"
              prefix={<span className="text-sm font-medium">Rp</span>}
              {...register('base_salary', { valueAsNumber: true })}
              error={errors.base_salary?.message}
              placeholder="0"
            />
            <Input
              label="Tanggal Efektif Gaji"
              type="date"
              {...register('base_salary_effective_date')}
              error={errors.base_salary_effective_date?.message}
            />
            <Input
              label="No. NPWP"
              {...register('npwp_number')}
              error={errors.npwp_number?.message}
              placeholder="Masukkan No. NPWP"
            />
          </div>
        )}

        {/* Tab 4: BPJS & Bank */}
        {activeTab === 'bpjs' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="No. BPJS Kesehatan"
              {...register('bpjs_kes_number')}
              error={errors.bpjs_kes_number?.message}
              placeholder="Masukkan No. BPJS Kesehatan"
            />
            <Input
              label="No. BPJS Ketenagakerjaan"
              {...register('bpjs_tk_number')}
              error={errors.bpjs_tk_number?.message}
              placeholder="Masukkan No. BPJS TK"
            />
            <Input
              label="Nama Bank"
              {...register('bank_name')}
              error={errors.bank_name?.message}
              placeholder="Contoh: BCA, Mandiri"
            />
            <Input
              label="No. Rekening"
              {...register('bank_account_number')}
              error={errors.bank_account_number?.message}
              placeholder="Masukkan No. Rekening"
            />
            <Input
              label="Nama Pemilik Rekening"
              {...register('bank_account_name')}
              error={errors.bank_account_name?.message}
              placeholder="Nama sesuai buku tabungan"
            />
          </div>
        )}

        {/* Tab 5: Tunjangan */}
        {activeTab === 'allowances' && mode === 'edit' && employeeId && (
          <EmployeeAllowances employeeId={employeeId} />
        )}
        {activeTab === 'allowances' && mode === 'create' && (
          <div className="text-center py-12 text-sm text-gray-500">
            Simpan data karyawan terlebih dahulu untuk mengatur tunjangan.
          </div>
        )}

        {/* Tab 6: Alamat */}
        {activeTab === 'address' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="col-span-1 md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Alamat Lengkap
              </label>
              <textarea
                {...register('address_street')}
                rows={3}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Masukkan alamat lengkap"
              />
              {errors.address_street && (
                <p className="mt-1 text-sm text-red-600">{errors.address_street.message}</p>
              )}
            </div>
            <Input
              label="Kota"
              {...register('address_city')}
              error={errors.address_city?.message}
              placeholder="Masukkan kota"
            />
            <Input
              label="Provinsi"
              {...register('address_province')}
              error={errors.address_province?.message}
              placeholder="Masukkan provinsi"
            />
            <Input
              label="Kode Pos"
              {...register('address_postal_code')}
              error={errors.address_postal_code?.message}
              placeholder="Masukkan kode pos"
            />
          </div>
        )}
      </div>

      {/* Form Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <Button
          type="button"
          variant="secondary"
          onClick={() => router.push('/employees')}
        >
          Batal
        </Button>
        <Button type="submit" variant="primary" loading={isSubmitting}>
          Simpan
        </Button>
      </div>
    </form>
  );
}
