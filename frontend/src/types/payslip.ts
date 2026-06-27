export interface PayslipRecord {
  id: number;
  year: number;
  month: number;
  employee_code: string;
  employee_name: string;
  gross_salary: number;
  net_salary: number;
  status: string;
  generated_at: string | null;
}

export interface AnnualSummaryMonth {
  month: number;
  month_name: string;
  gross_salary: number;
  total_deductions: number;
  pph21_tax: number;
  bpjs_total: number;
  net_salary: number;
}

export interface AnnualSummaryResponse {
  employee_id: number;
  employee_name: string;
  year: number;
  months: AnnualSummaryMonth[];
  ytd_gross: number;
  ytd_deductions: number;
  ytd_tax: number;
  ytd_bpjs: number;
  ytd_net: number;
}

export interface JobStatus {
  job_id: string;
  status: string;
  total_count: number;
  completed_count: number;
  failed_count: number;
  progress_percent: number;
  result_file_url: string | null;
  error_message: string | null;
}

export interface PayslipNotification {
  id: number;
  notification_type: string;
  title: string;
  message: string | null;
  link: string | null;
  is_read: boolean;
  created_at: string;
}
