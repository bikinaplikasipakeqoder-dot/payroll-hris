import { z } from 'zod';

export const employeeFormSchema = z.object({
  // Tab 1: Personal Data
  first_name: z.string().min(1, 'Nama depan wajib diisi').max(100),
  last_name: z.string().max(100).optional().or(z.literal('')),
  gender: z.enum(['M', 'F']).optional().nullable(),
  date_of_birth: z.string().optional().or(z.literal('')),
  personal_id_number: z.string().max(50).optional().or(z.literal('')),
  phone: z.string().max(20).optional().or(z.literal('')),
  email: z.string().email('Format email tidak valid').optional().or(z.literal('')),

  // Tab 2: Employment
  employee_code: z.string().min(1, 'Kode karyawan wajib diisi').max(50),
  date_joined: z.string().min(1, 'Tanggal bergabung wajib diisi'),
  department_id: z.number().optional().nullable(),
  position_id: z.number().optional().nullable(),
  grade_id: z.number().optional().nullable(),
  employment_status_id: z.number().optional().nullable(),
  entity_id: z.number().optional().nullable(),
  ptkp_status: z.enum(['TK/0', 'TK/1', 'TK/2', 'TK/3', 'K/0', 'K/1', 'K/2', 'K/3']),
  religion: z.enum(['Islam', 'Protestan', 'Katolik', 'Hindu', 'Buddha', 'Konghucu']).optional().or(z.literal('')),

  // Tab 3: Salary & Tax
  base_salary: z.number().positive('Gaji harus lebih dari 0').optional().nullable(),
  npwp_number: z.string().max(50).optional().or(z.literal('')),

  // Tab 4: BPJS & Bank
  bpjs_kes_number: z.string().max(30).optional().or(z.literal('')),
  bpjs_tk_number: z.string().max(30).optional().or(z.literal('')),
  bank_name: z.string().max(100).optional().or(z.literal('')),
  bank_account_number: z.string().max(50).optional().or(z.literal('')),
  bank_account_name: z.string().max(255).optional().or(z.literal('')),

  // Tab 5: Address
  address_street: z.string().optional().or(z.literal('')),
  address_city: z.string().max(100).optional().or(z.literal('')),
  address_province: z.string().max(100).optional().or(z.literal('')),
  address_postal_code: z.string().max(10).optional().or(z.literal('')),
});

export type EmployeeFormData = z.infer<typeof employeeFormSchema>;
