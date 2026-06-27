'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import { Employee } from '@/types';
import Card from '@/components/ui/Card';
import EmployeeForm from '@/components/employees/EmployeeForm';
import { EmployeeFormData } from '@/components/employees/EmployeeFormSchema';

export default function NewEmployeePage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: EmployeeFormData) => {
    setIsSubmitting(true);
    setError(null);
    try {
      await api.post<Employee>('/api/v1/employees', {
        company_id: 1,
        ...data,
      });
      alert('Karyawan berhasil ditambahkan');
      router.push('/employees');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Terjadi kesalahan saat menyimpan data');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Tambah Karyawan Baru</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      <Card>
        <EmployeeForm
          mode="create"
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
        />
      </Card>
    </div>
  );
}
