"""
Payslip builder service.
Constructs Payslip and PayslipLine ORM objects from calculation results.
"""
import json
from decimal import Decimal
from typing import List, Optional

from app.models.payroll import Payslip, PayslipLine
from app.calculations.allowance import AllowanceResult
from app.calculations.bpjs import BpjsResult
from app.services.attendance_loader import EmployeeAttendanceData, AttendanceSummary
from app.services.employee_loader import EmployeePayrollData
from app.utils.decimal_utils import to_decimal


class PayslipBuilder:
    """Builds Payslip and PayslipLine ORM instances from calculation results."""

    @staticmethod
    def build_payslip(
        payroll_run_id: int,
        employee_data: EmployeePayrollData,
        payroll_period: str,
        allowance_result: AllowanceResult,
        overtime_total: Decimal,
        bpjs_result: BpjsResult,
        pph21_tax: Decimal,
        tax_allowance: Decimal,
        net_salary: Decimal,
        gross_salary: Decimal,
        attendance_data: Optional[EmployeeAttendanceData] = None,
        kasbon_deduction: Decimal = Decimal("0"),
        other_deductions: Decimal = Decimal("0"),
    ) -> Payslip:
        """Build a complete Payslip with all PayslipLine entries.

        Args:
            payroll_run_id: ID of the parent payroll run
            employee_data: Employee compensation data
            payroll_period: Period string (YYYY-MM)
            allowance_result: Calculated allowance results
            overtime_total: Total overtime pay
            bpjs_result: BPJS calculation result
            pph21_tax: PPh 21 tax amount
            tax_allowance: Tax allowance for NETT method (0 for GROSS)
            net_salary: Final net take-home pay
            gross_salary: Total gross salary
            attendance_data: Attendance summary data
            kasbon_deduction: Kasbon installment deduction
            other_deductions: Other deductions

        Returns:
            Payslip ORM instance with populated lines
        """
        payslip_number = f"PSL-{payroll_period}-{employee_data.employee_code}"

        # Compute total deductions
        total_deductions = (
            pph21_tax
            + bpjs_result.total_employee
            + kasbon_deduction
            + other_deductions
        )

        # Get attendance summary
        summary = attendance_data.summary if attendance_data else AttendanceSummary()
        overtime_hours = attendance_data.total_overtime_hours if attendance_data else Decimal("0")

        # Build allowances and deductions detail JSON
        allowances_detail = json.dumps(allowance_result.details, default=str)

        deductions_items = []
        if kasbon_deduction > Decimal("0"):
            deductions_items.append({"name": "Kasbon", "amount": str(kasbon_deduction)})
        if other_deductions > Decimal("0"):
            deductions_items.append({"name": "Other Deductions", "amount": str(other_deductions)})
        deductions_detail = json.dumps(deductions_items, default=str)

        payslip = Payslip(
            payroll_run_id=payroll_run_id,
            employee_id=employee_data.employee_id,
            payslip_number=payslip_number,
            basic_salary=employee_data.base_salary,
            total_allowances=allowance_result.total_allowances,
            overtime_amount=overtime_total,
            bonus_amount=employee_data.approved_bonuses,
            gross_salary=gross_salary + tax_allowance,
            bpjs_kes_employee=bpjs_result.kes_employee,
            bpjs_jht_employee=bpjs_result.jht_employee,
            bpjs_jp_employee=bpjs_result.jp_employee,
            pph21_tax=pph21_tax,
            kasbon_deduction=kasbon_deduction,
            other_deductions=other_deductions,
            total_deductions=total_deductions,
            net_salary=net_salary,
            tax_allowance=tax_allowance,
            working_days=summary.working_days,
            overtime_hours=overtime_hours,
            late_minutes=summary.late_minutes,
            sick_days=summary.sick_days,
            leave_days=summary.leave_days,
            allowances_detail=allowances_detail,
            deductions_detail=deductions_detail,
            is_approved=False,
        )

        # Build payslip lines
        lines = PayslipBuilder._build_lines(
            employee_data=employee_data,
            allowance_result=allowance_result,
            overtime_total=overtime_total,
            bpjs_result=bpjs_result,
            pph21_tax=pph21_tax,
            tax_allowance=tax_allowance,
            net_salary=net_salary,
            kasbon_deduction=kasbon_deduction,
            other_deductions=other_deductions,
        )
        payslip.lines = lines

        return payslip

    @staticmethod
    def _build_lines(
        employee_data: EmployeePayrollData,
        allowance_result: AllowanceResult,
        overtime_total: Decimal,
        bpjs_result: BpjsResult,
        pph21_tax: Decimal,
        tax_allowance: Decimal,
        net_salary: Decimal,
        kasbon_deduction: Decimal,
        other_deductions: Decimal,
    ) -> List[PayslipLine]:
        """Build all PayslipLine entries for a payslip.

        Sort order convention:
        - Earnings: 10-99
        - BPJS: 100-199
        - TAX: 200-299
        - Deductions: 300-399
        - NET: 900
        """
        lines = []
        sort_order = 10

        # --- EARNINGS ---
        # Basic Salary
        lines.append(PayslipLine(
            line_type="EARNING",
            category="BASIC",
            description="Basic Salary",
            amount=employee_data.base_salary,
            sort_order=sort_order,
        ))
        sort_order += 1

        # Each allowance
        for detail in allowance_result.details:
            lines.append(PayslipLine(
                line_type="EARNING",
                category="ALLOWANCE",
                description=detail["name"],
                amount=to_decimal(detail["amount"]),
                sort_order=sort_order,
            ))
            sort_order += 1

        # Overtime
        if overtime_total > Decimal("0"):
            lines.append(PayslipLine(
                line_type="EARNING",
                category="OVERTIME",
                description="Overtime",
                amount=overtime_total,
                sort_order=sort_order,
            ))
            sort_order += 1

        # Bonus
        if employee_data.approved_bonuses > Decimal("0"):
            lines.append(PayslipLine(
                line_type="EARNING",
                category="BONUS",
                description="Bonus",
                amount=employee_data.approved_bonuses,
                sort_order=sort_order,
            ))
            sort_order += 1

        # Tax allowance (NETT method only)
        if tax_allowance > Decimal("0"):
            lines.append(PayslipLine(
                line_type="EARNING",
                category="TAX_ALLOWANCE",
                description="Tunjangan Pajak",
                amount=tax_allowance,
                sort_order=sort_order,
            ))
            sort_order += 1

        # --- BPJS (employee portions) ---
        sort_order = 100
        if bpjs_result.kes_employee > Decimal("0"):
            lines.append(PayslipLine(
                line_type="BPJS",
                category="KESEHATAN",
                description="BPJS Kesehatan (Pemotongan Karyawan)",
                amount=bpjs_result.kes_employee,
                sort_order=sort_order,
            ))
            sort_order += 1

        if bpjs_result.jht_employee > Decimal("0"):
            lines.append(PayslipLine(
                line_type="BPJS",
                category="JHT",
                description="BPJS JHT (Pemotongan Karyawan)",
                amount=bpjs_result.jht_employee,
                sort_order=sort_order,
            ))
            sort_order += 1

        if bpjs_result.jp_employee > Decimal("0"):
            lines.append(PayslipLine(
                line_type="BPJS",
                category="JP",
                description="BPJS JP (Pemotongan Karyawan)",
                amount=bpjs_result.jp_employee,
                sort_order=sort_order,
            ))
            sort_order += 1

        # --- BPJS (employer portions, informational) ---
        sort_order = 110
        if bpjs_result.kes_employer > Decimal("0"):
            lines.append(PayslipLine(
                line_type="BPJS",
                category="EMPLOYER_KESEHATAN",
                description="BPJS Kesehatan (Tanggungan Perusahaan)",
                amount=bpjs_result.kes_employer,
                sort_order=sort_order,
            ))
            sort_order += 1

        if bpjs_result.jht_employer > Decimal("0"):
            lines.append(PayslipLine(
                line_type="BPJS",
                category="EMPLOYER_JHT",
                description="BPJS JHT (Tanggungan Perusahaan)",
                amount=bpjs_result.jht_employer,
                sort_order=sort_order,
            ))
            sort_order += 1

        if bpjs_result.jp_employer > Decimal("0"):
            lines.append(PayslipLine(
                line_type="BPJS",
                category="EMPLOYER_JP",
                description="BPJS JP (Tanggungan Perusahaan)",
                amount=bpjs_result.jp_employer,
                sort_order=sort_order,
            ))
            sort_order += 1

        if bpjs_result.jkk_employer > Decimal("0"):
            lines.append(PayslipLine(
                line_type="BPJS",
                category="JKK",
                description="BPJS JKK (Tanggungan Perusahaan)",
                amount=bpjs_result.jkk_employer,
                sort_order=sort_order,
            ))
            sort_order += 1

        if bpjs_result.jkm_employer > Decimal("0"):
            lines.append(PayslipLine(
                line_type="BPJS",
                category="JKM",
                description="BPJS JKM (Tanggungan Perusahaan)",
                amount=bpjs_result.jkm_employer,
                sort_order=sort_order,
            ))
            sort_order += 1

        # --- TAX ---
        sort_order = 200
        lines.append(PayslipLine(
            line_type="TAX",
            category="PPH21",
            description="PPh 21",
            amount=pph21_tax,
            sort_order=sort_order,
        ))

        # --- DEDUCTIONS ---
        sort_order = 300
        if kasbon_deduction > Decimal("0"):
            lines.append(PayslipLine(
                line_type="DEDUCTION",
                category="KASBON",
                description="Kasbon Deduction",
                amount=kasbon_deduction,
                sort_order=sort_order,
            ))
            sort_order += 1

        if other_deductions > Decimal("0"):
            lines.append(PayslipLine(
                line_type="DEDUCTION",
                category="OTHER",
                description="Other Deductions",
                amount=other_deductions,
                sort_order=sort_order,
            ))
            sort_order += 1

        # --- NET ---
        lines.append(PayslipLine(
            line_type="NET",
            category="NET_SALARY",
            description="Net Salary",
            amount=net_salary,
            sort_order=900,
        ))

        return lines
