'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import { Employee } from '@/types';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import EmployeeForm from '@/components/employees/EmployeeForm';
import { EmployeeFormData } from '@/components/employees/EmployeeFormSchema';

export default function EditEmployeePage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEmployee = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.get<Employee>(`/api/v1/employees/${id}`);
        setEmployee(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('Terjadi kesalahan saat memuat data karyawan');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchEmployee();
  }, [id]);

  const handleSubmit = async (data: EmployeeFormData) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await api.patch<Employee>(`/api/v1/employees/${id}`, data);
      alert('Data karyawan berhasil diperbarui');
      router.push('/employees');
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Terjadi kesalahan saat menyimpan data');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const mapEmployeeToFormData = (emp: Employee): Partial<EmployeeFormData> => ({
    first_name: emp.first_name,
    last_name: emp.last_name || '',
    gender: emp.gender as 'M' | 'F' | null,
    date_of_birth: emp.date_of_birth || '',
    personal_id_number: emp.personal_id_number || '',
    phone: emp.phone || '',
    email: emp.email || '',
    employee_code: emp.employee_code,
    date_joined: emp.date_joined,
    department_id: emp.department_id,
    position_id: emp.position_id,
    grade_id: emp.grade_id,
    employment_status_id: emp.employment_status_id,
    ptkp_status: emp.ptkp_status as EmployeeFormData['ptkp_status'],
    religion: (emp.religion as EmployeeFormData['religion']) || 'Islam',
    base_salary: emp.base_salary,
    npwp_number: emp.npwp || '',
    bpjs_kes_number: emp.bpjs_kesehatan_number || '',
    bpjs_tk_number: emp.bpjs_ketenagakerjaan_number || '',
    bank_name: emp.bank_name || '',
    bank_account_number: emp.bank_account_number || '',
    bank_account_name: emp.bank_account_holder_name || '',
    address_street: emp.address_street || '',
    address_city: emp.address_city || '',
    address_province: emp.address_province || '',
    address_postal_code: emp.address_postal_code || '',
  });

  if (loading) {
    return (
      <div className="text-center py-12 text-gray-500">Memuat data...</div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <Button variant="secondary" onClick={() => router.push('/employees')}>
          Kembali ke Daftar
        </Button>
      </div>
    );
  }

  if (!employee) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">
        Edit Karyawan: {employee.full_name}
      </h1>

      {submitError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {submitError}
        </div>
      )}

      <Card>
        <EmployeeForm
          mode="edit"
          employeeId={employee.id}
          defaultValues={mapEmployeeToFormData(employee)}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
        />
      </Card>
    </div>
  );
}
