export interface Employee {
  id: number;
  company_id: number;
  employee_code: string;
  first_name: string;
  last_name: string | null;
  full_name: string;
  date_of_birth: string | null;
  gender: string | null;
  personal_id_number: string | null;
  npwp: string | null;
  ptkp_status: string;
  religion: string | null;
  phone: string | null;
  email: string | null;
  address_street: string | null;
  address_city: string | null;
  address_province: string | null;
  address_postal_code: string | null;
  department_id: number | null;
  position_id: number | null;
  grade_id: number | null;
  employment_status_id: number | null;
  entity_id: number | null;
  date_joined: string;
  date_left: string | null;
  bank_name: string | null;
  bank_account_number: string | null;
  bank_account_holder_name: string | null;
  base_salary: number | null;
  base_salary_effective_date: string | null;
  bpjs_kesehatan_number: string | null;
  bpjs_ketenagakerjaan_number: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface EmployeeCreate {
  company_id: number;
  employee_code: string;
  first_name: string;
  last_name?: string | null;
  personal_id_number?: string | null;
  npwp_number?: string | null;
  ptkp_status?: string;
  religion?: string | null;
  gender?: string | null;
  date_of_birth?: string | null;
  date_joined: string;
  department_id?: number | null;
  position_id?: number | null;
  grade_id?: number | null;
  employment_status_id?: number | null;
  entity_id?: number | null;
  base_salary?: number | null;
  base_salary_effective_date?: string | null;
  bank_name?: string | null;
  bank_account_number?: string | null;
  bank_account_name?: string | null;
  bpjs_kes_number?: string | null;
  bpjs_tk_number?: string | null;
  phone?: string | null;
  email?: string | null;
  address_street?: string | null;
  address_city?: string | null;
  address_province?: string | null;
  address_postal_code?: string | null;
}

export interface PayrollRun {
  id: number;
  company_id: number;
  period_month: number;
  period_year: number;
  run_date: string;
  status: 'DRAFT' | 'PROCESSING' | 'COMPLETED' | 'APPROVED' | 'PAID';
  total_gross: number;
  total_deductions: number;
  total_net: number;
  employee_count: number;
  created_at: string;
}

export interface EmployeeAllowance {
  id: number;
  employee_id: number;
  allowance_type_id: number;
  allowance_type_name: string;
  allowance_type_code: string;
  amount: number;
  effective_date: string;
  end_date: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface Entity {
  id: number;
  company_id: number;
  code: string;
  name: string;
  address: string | null;
  city: string | null;
  province: string | null;
  postal_code: string | null;
  country: string | null;
  phone: string | null;
  email: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface UmpSetting {
  id: number;
  company_id: number;
  province: string;
  city: string | null;
  amount: number;
  effective_date: string;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface DashboardStats {
  totalEmployees: number;
  activePayrollRuns: number;
  pendingOvertimeApprovals: number;
  totalPayrollThisMonth: number;
}

export interface RuleCategory {
  id: number;
  category_code: string;
  category_name: string;
  description: string | null;
  is_active: boolean;
}

export type RuleType = 'FORMULA' | 'CONSTANT' | 'BRACKET' | 'LOOKUP_TABLE';

export interface RuleConfiguration {
  id: number;
  company_id: number;
  category_id: number;
  category_code: string;
  category_name: string;
  rule_code: string;
  rule_name: string;
  rule_type: RuleType;
  formula: string | null;
  value: number | null;
  min_value: number | null;
  max_value: number | null;
  rate: number | null;
  effective_date: string;
  expiry_date: string | null;
  priority: number;
  is_active: boolean;
  description: string | null;
  created_by: number | null;
  updated_by: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface RuleAuditLog {
  id: number;
  rule_id: number;
  action: string;
  old_value: string | null;
  new_value: string | null;
  changed_by: number;
  changed_by_name: string | null;
  changed_at: string;
  reason: string | null;
}
