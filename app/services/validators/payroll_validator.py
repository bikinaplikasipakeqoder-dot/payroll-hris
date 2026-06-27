"""
Payroll business rule validators.
Validates preconditions before payroll processing begins.
"""
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.payroll import PayrollRun
from app.exceptions import (
    PayrollValidationError,
    DuplicatePayrollRunError,
)


def validate_payroll_run_creation(
    company_id: int, payroll_period: str, session: Session
) -> None:
    """Check no duplicate payroll run exists for company + period.

    Raises:
        DuplicatePayrollRunError: If a payroll run already exists for this period.
    """
    existing = session.query(PayrollRun).filter(
        PayrollRun.company_id == company_id,
        PayrollRun.payroll_period == payroll_period,
    ).first()

    if existing:
        raise DuplicatePayrollRunError(
            f"Payroll run already exists for period {payroll_period}",
            {"company_id": company_id, "payroll_period": payroll_period, "existing_id": existing.id},
        )


def validate_payroll_run_processing(payroll_run: PayrollRun, session: Session) -> None:
    """Validate a payroll run is eligible for processing.

    Checks:
    - Status must be DRAFT
    - At least one active employee must exist (checked later during load)

    Raises:
        PayrollValidationError: If run is not in DRAFT status.
    """
    if payroll_run.status != "DRAFT":
        raise PayrollValidationError(
            f"Payroll run must be in DRAFT status to process. Current status: {payroll_run.status}",
            {"payroll_run_id": payroll_run.id, "current_status": payroll_run.status},
        )


def validate_employee_for_payroll(employee_data) -> list:
    """Validate an employee's data is sufficient for payroll calculation.

    Checks:
    - PTKP status is set (non-empty)
    - Base salary is greater than 0

    Args:
        employee_data: EmployeePayrollData instance

    Returns:
        List of warning messages (empty if valid).
        Non-critical issues return warnings; critical issues raise exceptions.
    """
    warnings = []

    if not employee_data.ptkp_status:
        warnings.append(
            f"Employee {employee_data.employee_code}: PTKP status not set"
        )

    if employee_data.base_salary <= Decimal("0"):
        warnings.append(
            f"Employee {employee_data.employee_code}: Base salary is zero or negative"
        )

    return warnings
