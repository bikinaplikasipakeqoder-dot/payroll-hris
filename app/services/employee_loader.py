"""
Employee data loader for batch payroll processing.
Uses SQLAlchemy eager loading to avoid N+1 queries.
"""
from decimal import Decimal
from datetime import date
from typing import List
from dataclasses import dataclass, field
from sqlalchemy.orm import Session, selectinload

from app.models.employee import Employee
from app.models.salary import (
    AllowanceType,
    EmployeeAllowance,
    AllowanceGradeMatrix,
    AllowancePositionMatrix,
    AllowanceDepartmentMatrix,
    EmployeeSalaryHistory,
)
from app.models.bonus import Bonus, Reimbursement
from app.models.kasbon import KasbonInstallment, KasbonRequest
from app.utils.decimal_utils import to_decimal
from app.calculations.allowance import AllowanceEntry


@dataclass
class EmployeePayrollData:
    """All data needed to calculate one employee's payslip."""
    employee_id: int
    employee_code: str
    first_name: str
    last_name: str
    ptkp_status: str
    base_salary: Decimal
    allowances: List[AllowanceEntry] = field(default_factory=list)
    approved_bonuses: Decimal = Decimal("0")
    kasbon_due: Decimal = Decimal("0")
    reimbursements_taxable: Decimal = Decimal("0")
    reimbursements_non_taxable: Decimal = Decimal("0")


class EmployeeLoader:
    """Loads all active employees with their compensation data."""

    @staticmethod
    def _cutoff_date(period_start: date) -> date:
        """Cutoff: employees who joined on or before the 15th of the period month are paid."""
        return date(period_start.year, period_start.month, 15)

    @staticmethod
    def load_all(
        company_id: int,
        period_start: date,
        period_end: date,
        session: Session,
    ) -> List[EmployeePayrollData]:
        """Load all active employees with allowances, bonuses, and kasbon.

        Uses eager loading to minimize database queries.
        Only employees whose date_joined <= 15th of the period month are included.
        """
        cutoff = EmployeeLoader._cutoff_date(period_start)
        # Query active employees with eager-loaded allowances
        employees = session.query(Employee).filter(
            Employee.company_id == company_id,
            Employee.is_active == True,
            Employee.date_joined <= cutoff,
        ).options(
            selectinload(Employee.employee_allowances).selectinload(
                EmployeeAllowance.allowance_type
            ),
            selectinload(Employee.salary_history),
        ).all()

        if not employees:
            return []

        employee_ids = [e.id for e in employees]

        # Load approved bonuses for the period
        bonuses = session.query(Bonus).filter(
            Bonus.employee_id.in_(employee_ids),
            Bonus.approval_status == "APPROVED",
            Bonus.bonus_date >= period_start,
            Bonus.bonus_date <= period_end,
            Bonus.payroll_run_id.is_(None),  # Not yet processed
        ).all()
        bonus_by_emp: dict = {}
        for b in bonuses:
            bonus_by_emp.setdefault(b.employee_id, Decimal("0"))
            bonus_by_emp[b.employee_id] += to_decimal(b.amount)

        # Load approved reimbursements for the period (join to type for is_taxable)
        reimbursements = session.query(Reimbursement).filter(
            Reimbursement.employee_id.in_(employee_ids),
            Reimbursement.approval_status == "APPROVED",
            Reimbursement.claim_date >= period_start,
            Reimbursement.claim_date <= period_end,
            Reimbursement.payroll_run_id.is_(None),  # Not yet processed
        ).options(
            selectinload(Reimbursement.reimbursement_type),
        ).all()
        reimb_taxable_by_emp: dict = {}
        reimb_nontax_by_emp: dict = {}
        for r in reimbursements:
            # Use approved_amount if available, otherwise claim_amount
            amount = to_decimal(r.approved_amount) if r.approved_amount else to_decimal(r.claim_amount)
            # Taxability comes from the reimbursement type
            is_taxable = r.reimbursement_type.is_taxable if r.reimbursement_type else False
            if is_taxable:
                reimb_taxable_by_emp.setdefault(r.employee_id, Decimal("0"))
                reimb_taxable_by_emp[r.employee_id] += amount
            else:
                reimb_nontax_by_emp.setdefault(r.employee_id, Decimal("0"))
                reimb_nontax_by_emp[r.employee_id] += amount

        # Load kasbon installments due in period
        kasbon_installments = session.query(KasbonInstallment).join(
            KasbonRequest,
            KasbonInstallment.kasbon_request_id == KasbonRequest.id,
        ).filter(
            KasbonRequest.employee_id.in_(employee_ids),
            KasbonInstallment.due_date >= period_start,
            KasbonInstallment.due_date <= period_end,
            KasbonInstallment.is_paid == False,
        ).all()
        # Map installment -> employee via kasbon_request
        kasbon_request_ids = [ki.kasbon_request_id for ki in kasbon_installments]
        kasbon_req_to_emp: dict = {}
        if kasbon_request_ids:
            kasbon_requests = session.query(KasbonRequest).filter(
                KasbonRequest.id.in_(kasbon_request_ids),
            ).all()
            kasbon_req_to_emp = {kr.id: kr.employee_id for kr in kasbon_requests}
        kasbon_by_emp: dict = {}
        for ki in kasbon_installments:
            emp_id = kasbon_req_to_emp.get(ki.kasbon_request_id)
            if emp_id:
                kasbon_by_emp.setdefault(emp_id, Decimal("0"))
                kasbon_by_emp[emp_id] += to_decimal(ki.amount)

        # Load all active allowance types for the company
        allowance_types = session.query(AllowanceType).filter(
            AllowanceType.company_id == company_id,
            AllowanceType.is_active == True,
        ).all()

        # Load matrix rows for all relevant allowance types in one query per basis
        grade_matrix = session.query(AllowanceGradeMatrix).filter(
            AllowanceGradeMatrix.allowance_type_id.in_([at.id for at in allowance_types]),
            AllowanceGradeMatrix.is_active == True,
        ).all()
        position_matrix = session.query(AllowancePositionMatrix).filter(
            AllowancePositionMatrix.allowance_type_id.in_([at.id for at in allowance_types]),
            AllowancePositionMatrix.is_active == True,
        ).all()
        department_matrix = session.query(AllowanceDepartmentMatrix).filter(
            AllowanceDepartmentMatrix.allowance_type_id.in_([at.id for at in allowance_types]),
            AllowanceDepartmentMatrix.is_active == True,
        ).all()

        # Build lookup maps: (allowance_type_id, entity_id) -> list of rows
        grade_map: dict = {}
        for row in grade_matrix:
            grade_map.setdefault((row.allowance_type_id, row.grade_id), []).append(row)
        position_map: dict = {}
        for row in position_matrix:
            position_map.setdefault((row.allowance_type_id, row.position_id), []).append(row)
        department_map: dict = {}
        for row in department_matrix:
            department_map.setdefault((row.allowance_type_id, row.department_id), []).append(row)

        def _is_in_period(row, period_start: date, period_end: date) -> bool:
            if row.effective_date > period_end:
                return False
            if row.end_date and row.end_date < period_start:
                return False
            return True

        def _pick_matrix_row(rows, period_start: date, period_end: date):
            valid = [r for r in rows if _is_in_period(r, period_start, period_end)]
            if not valid:
                return None
            return max(valid, key=lambda r: r.effective_date)

        def _pick_base_salary(history_rows, period_end: date):
            valid = [
                r for r in history_rows
                if r.is_active and r.effective_date <= period_end and (r.end_date is None or r.end_date >= period_end)
            ]
            if not valid:
                # Fallback to the most recent record before period_end
                past = [r for r in history_rows if r.is_active and r.effective_date <= period_end]
                if past:
                    return max(past, key=lambda r: r.effective_date).base_salary
                return Decimal("0")
            return max(valid, key=lambda r: r.effective_date).base_salary

        # Build EmployeePayrollData list
        result = []
        for emp in employees:
            # Build allowance entries (active ones only)
            allowances = []

            # 1. Individual assignments
            for ea in emp.employee_allowances:
                if not ea.is_active:
                    continue
                if ea.effective_date > period_end:
                    continue
                if ea.end_date and ea.end_date < period_start:
                    continue
                at = ea.allowance_type
                if not at or not at.is_active:
                    continue
                if at.amount_basis != "INDIVIDUAL":
                    continue
                allowances.append(AllowanceEntry(
                    name=at.name,
                    code=at.code,
                    calculation_type=at.calculation_type,
                    amount=to_decimal(ea.amount),
                    is_taxable=at.is_taxable,
                    is_bpjs_base=at.is_bpjs_base,
                ))

            # 2. Matrix-based assignments (GRADE / POSITION / DEPARTMENT)
            for at in allowance_types:
                if at.amount_basis == "UNIVERSAL":
                    continue
                if at.amount_basis == "INDIVIDUAL":
                    continue

                matrix_row = None
                if at.amount_basis == "GRADE" and emp.grade_id:
                    matrix_row = _pick_matrix_row(
                        grade_map.get((at.id, emp.grade_id), []), period_start, period_end
                    )
                elif at.amount_basis == "POSITION" and emp.position_id:
                    matrix_row = _pick_matrix_row(
                        position_map.get((at.id, emp.position_id), []), period_start, period_end
                    )
                elif at.amount_basis == "DEPARTMENT" and emp.department_id:
                    matrix_row = _pick_matrix_row(
                        department_map.get((at.id, emp.department_id), []), period_start, period_end
                    )

                if matrix_row:
                    allowances.append(AllowanceEntry(
                        name=at.name,
                        code=at.code,
                        calculation_type=at.calculation_type,
                        amount=to_decimal(matrix_row.amount),
                        is_taxable=at.is_taxable,
                        is_bpjs_base=at.is_bpjs_base,
                    ))

            result.append(EmployeePayrollData(
                employee_id=emp.id,
                employee_code=emp.employee_code,
                first_name=emp.first_name,
                last_name=emp.last_name or "",
                ptkp_status=emp.ptkp_status,
                base_salary=to_decimal(_pick_base_salary(emp.salary_history, period_end)),
                allowances=allowances,
                approved_bonuses=bonus_by_emp.get(emp.id, Decimal("0")),
                kasbon_due=kasbon_by_emp.get(emp.id, Decimal("0")),
                reimbursements_taxable=reimb_taxable_by_emp.get(emp.id, Decimal("0")),
                reimbursements_non_taxable=reimb_nontax_by_emp.get(emp.id, Decimal("0")),
            ))

        return result

    @staticmethod
    def count_eligible(
        company_id: int,
        period_start: date,
        period_end: date,
        session: Session,
    ) -> int:
        """Return the number of active employees eligible for payroll in a period."""
        cutoff = EmployeeLoader._cutoff_date(period_start)
        return session.query(Employee).filter(
            Employee.company_id == company_id,
            Employee.is_active == True,
            Employee.date_joined <= cutoff,
        ).count()
