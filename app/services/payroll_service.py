"""
Payroll Service Orchestrator.
Coordinates the entire payroll processing pipeline:
creation, calculation, approval, and retrieval of payroll runs.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.payroll import PayrollRun, Payslip
from app.models.employee import Employee
from app.models.tax import TaxSetting
from app.exceptions import (
    PayrollRunError,
    PayrollValidationError,
)
from app.utils.date_utils import parse_payroll_period, get_month_range
from app.utils.decimal_utils import to_decimal, round_money

# Calculation modules
from app.calculations.allowance import calculate_all_allowances
from app.calculations.overtime import calculate_overtime_total
from app.calculations.bpjs import calculate_all_bpjs, calculate_bpjs_base
from app.calculations.pph21_pasal17 import calculate_monthly_pph21_pasal17
from app.calculations.pph21_ter import (
    get_ter_category,
    find_ter_rate,
    calculate_monthly_pph21_ter,
)
from app.calculations.gross_nett import (
    calculate_gross_method,
    calculate_nett_method_grossup,
)

# Service modules
from app.services.config_loader import ConfigLoader
from app.services.employee_loader import EmployeeLoader, EmployeePayrollData
from app.services.attendance_loader import AttendanceLoader, EmployeeAttendanceData
from app.services.payslip_builder import PayslipBuilder
from app.services.validators.payroll_validator import (
    validate_payroll_run_creation,
    validate_payroll_run_processing,
    validate_employee_for_payroll,
)

logger = logging.getLogger(__name__)


class PayrollService:
    """Main payroll service orchestrator.

    Coordinates the end-to-end payroll processing pipeline including
    creation, batch calculation, approval, and retrieval of payroll runs.
    """

    VALID_PAYROLL_METHODS = {"GROSS", "GROSS_UP", "NETT"}

    @staticmethod
    def create_payroll_run(
        company_id: int,
        payroll_period: str,
        payroll_method: Optional[str],
        tax_method: str,
        created_by: int,
        session: Session,
    ) -> PayrollRun:
        """Create a new payroll run in DRAFT status.

        Steps:
        1. Validate no duplicate run exists for this company + period
        2. Resolve payroll_method from TaxSetting if not provided
        3. Parse period string into start/end dates
        4. Create and persist PayrollRun record

        Args:
            company_id: Company ID
            payroll_period: Period string (YYYY-MM format)
            payroll_method: GROSS, GROSS_UP, or NETT; defaults to company tax setting
            tax_method: PASAL_17 or TER
            created_by: User ID of creator
            session: SQLAlchemy session

        Returns:
            Created PayrollRun in DRAFT status

        Raises:
            DuplicatePayrollRunError: If run already exists for period
            PayrollValidationError: If payroll_method is invalid
        """
        # 1. Validate no duplicate
        validate_payroll_run_creation(company_id, payroll_period, session)

        # 2. Resolve payroll method
        resolved_method = payroll_method
        if resolved_method is None:
            tax_setting = (
                session.query(TaxSetting)
                .filter(TaxSetting.company_id == company_id, TaxSetting.is_active == True)
                .first()
            )
            resolved_method = tax_setting.payroll_method if tax_setting else "GROSS"

        if resolved_method not in PayrollService.VALID_PAYROLL_METHODS:
            raise PayrollValidationError(
                f"payroll_method must be one of {sorted(PayrollService.VALID_PAYROLL_METHODS)}"
            )

        # 3. Parse period
        year, month = parse_payroll_period(payroll_period)
        period_start, period_end = get_month_range(year, month)

        # 4. Create PayrollRun
        payroll_run = PayrollRun(
            company_id=company_id,
            payroll_period=payroll_period,
            period_start_date=period_start,
            period_end_date=period_end,
            payroll_method=resolved_method,
            tax_method=tax_method,
            status="DRAFT",
            created_by=created_by,
        )

        session.add(payroll_run)
        session.flush()

        logger.info(
            f"Created payroll run #{payroll_run.id} for company={company_id}, "
            f"period={payroll_period}, method={payroll_method}, tax={tax_method}"
        )

        return payroll_run

    @staticmethod
    def process_payroll_run(payroll_run_id: int, session: Session) -> PayrollRun:
        """Process entire payroll run — the main batch calculation.

        Flow:
        1. Validate run status == DRAFT, update to PROCESSING
        2. Load config via ConfigLoader
        3. Load employees via EmployeeLoader
        4. Load attendance via AttendanceLoader
        5. For each employee: calculate all components
        6. Bulk insert all payslips and lines
        7. Update payroll_run totals + status=COMPLETED
        8. Return updated PayrollRun

        ALL WITHIN A SINGLE TRANSACTION — rollback on any failure.
        """
        # Load payroll run
        payroll_run = session.query(PayrollRun).filter(
            PayrollRun.id == payroll_run_id
        ).first()
        if not payroll_run:
            raise PayrollRunError(
                f"Payroll run not found: {payroll_run_id}",
                {"payroll_run_id": payroll_run_id},
            )

        try:
            # 1. Validate and set status to PROCESSING
            validate_payroll_run_processing(payroll_run, session)
            payroll_run.status = "PROCESSING"
            session.flush()

            # 2. Load configuration
            config = ConfigLoader.load(
                company_id=payroll_run.company_id,
                period_date=payroll_run.period_start_date,
                session=session,
            )

            # 3. Load employees
            employees = EmployeeLoader.load_all(
                company_id=payroll_run.company_id,
                period_start=payroll_run.period_start_date,
                period_end=payroll_run.period_end_date,
                session=session,
            )

            if not employees:
                raise PayrollRunError(
                    "No active employees found for payroll processing",
                    {"company_id": payroll_run.company_id},
                )

            # 4. Load attendance
            employee_ids = [emp.employee_id for emp in employees]
            attendance_map = AttendanceLoader.load_period(
                company_id=payroll_run.company_id,
                employee_ids=employee_ids,
                period_start=payroll_run.period_start_date,
                period_end=payroll_run.period_end_date,
                session=session,
            )

            # 5. Process each employee
            payslips: List[Payslip] = []
            total_gross = Decimal("0")
            total_deductions = Decimal("0")
            total_tax = Decimal("0")
            total_net = Decimal("0")
            processed_count = 0

            for emp in employees:
                # Validate employee data
                warnings = validate_employee_for_payroll(emp)
                if warnings:
                    for w in warnings:
                        logger.warning(w)
                    # Skip employees with critical issues (no PTKP or zero salary)
                    if not emp.ptkp_status or emp.base_salary <= Decimal("0"):
                        logger.warning(
                            f"Skipping employee {emp.employee_code} due to validation issues"
                        )
                        continue

                payslip = PayrollService._process_single_employee(
                    emp=emp,
                    payroll_run=payroll_run,
                    config=config,
                    attendance_map=attendance_map,
                )
                payslips.append(payslip)

                total_gross += to_decimal(payslip.gross_salary)
                total_deductions += to_decimal(payslip.total_deductions)
                total_tax += to_decimal(payslip.pph21_tax)
                total_net += to_decimal(payslip.net_salary)
                processed_count += 1

            # 6. Bulk insert payslips (with their lines via relationship cascade)
            session.add_all(payslips)
            session.flush()

            # 7. Update payroll run totals
            payroll_run.total_employees = processed_count
            payroll_run.total_gross = total_gross
            payroll_run.total_deductions = total_deductions
            payroll_run.total_tax = total_tax
            payroll_run.total_net = total_net
            payroll_run.status = "COMPLETED"
            session.flush()

            logger.info(
                f"Payroll run #{payroll_run.id} completed: "
                f"{processed_count} employees, total_net={total_net}"
            )

            return payroll_run

        except Exception as e:
            # Rollback on any failure
            payroll_run.status = "DRAFT"
            session.flush()
            logger.error(f"Payroll run #{payroll_run_id} failed: {str(e)}")
            raise

    @staticmethod
    def process_payroll_batch(
        payroll_run_id: int,
        employee_ids: List[int],
        finalize: bool,
        session: Session,
    ) -> dict:
        """Process a batch of employees for a payroll run.

        This supports chunked frontend processing to stay within Vercel's
        10-second serverless function limit. Each call is idempotent for the
        given employee_ids (existing payslips for those IDs are replaced).

        Flow:
        1. Load payroll run; on first call (DRAFT) set status=PROCESSING
        2. Delete existing payslips for the requested employee_ids
        3. Load requested employees and their attendance
        4. Calculate payslips for each employee
        5. Insert payslips
        6. If finalize=True: compute totals from all payslips and set COMPLETED
        """
        from app.models.payroll import Payslip

        payroll_run = session.query(PayrollRun).filter(
            PayrollRun.id == payroll_run_id
        ).first()
        if not payroll_run:
            raise PayrollRunError(
                f"Payroll run not found: {payroll_run_id}",
                {"payroll_run_id": payroll_run_id},
            )

        if payroll_run.status == "DRAFT":
            validate_payroll_run_processing(payroll_run, session)
            payroll_run.status = "PROCESSING"
            session.flush()
        elif payroll_run.status != "PROCESSING":
            raise PayrollValidationError(
                f"Payroll run must be in DRAFT or PROCESSING status to process batch. Current: {payroll_run.status}",
                {"payroll_run_id": payroll_run_id, "current_status": payroll_run.status},
            )

        if not employee_ids:
            if finalize and payroll_run.status == "PROCESSING":
                PayrollService._finalize_payroll_run(payroll_run, session)
            return PayrollService._build_progress_response(payroll_run, session, 0)

        # Load config once per batch
        config = ConfigLoader.load(
            company_id=payroll_run.company_id,
            period_date=payroll_run.period_start_date,
            session=session,
        )

        # Load only requested employees
        employees = EmployeeLoader.load_by_ids(
            company_id=payroll_run.company_id,
            employee_ids=employee_ids,
            period_start=payroll_run.period_start_date,
            period_end=payroll_run.period_end_date,
            session=session,
        )

        # Load attendance for the requested employees
        attendance_map = AttendanceLoader.load_period(
            company_id=payroll_run.company_id,
            employee_ids=employee_ids,
            period_start=payroll_run.period_start_date,
            period_end=payroll_run.period_end_date,
            session=session,
        )

        # Delete existing payslips for these employees to keep batches idempotent
        session.query(Payslip).filter(
            Payslip.payroll_run_id == payroll_run_id,
            Payslip.employee_id.in_(employee_ids),
        ).delete(synchronize_session=False)

        # Process each employee
        payslips: List[Payslip] = []
        for emp in employees:
            warnings = validate_employee_for_payroll(emp)
            if warnings:
                for w in warnings:
                    logger.warning(w)
                if not emp.ptkp_status or emp.base_salary <= Decimal("0"):
                    logger.warning(
                        f"Skipping employee {emp.employee_code} due to validation issues"
                    )
                    continue

            payslip = PayrollService._process_single_employee(
                emp=emp,
                payroll_run=payroll_run,
                config=config,
                attendance_map=attendance_map,
            )
            payslips.append(payslip)

        session.add_all(payslips)
        session.flush()

        if finalize:
            PayrollService._finalize_payroll_run(payroll_run, session)

        return PayrollService._build_progress_response(
            payroll_run, session, len(payslips)
        )

    @staticmethod
    def _finalize_payroll_run(payroll_run: PayrollRun, session: Session) -> None:
        """Compute totals from all payslips and mark run as COMPLETED."""
        from app.models.payroll import Payslip

        row = session.query(
            session.func.count(Payslip.id).label("count"),
            session.func.coalesce(session.func.sum(Payslip.gross_salary), Decimal("0")).label("gross"),
            session.func.coalesce(session.func.sum(Payslip.total_deductions), Decimal("0")).label("deductions"),
            session.func.coalesce(session.func.sum(Payslip.pph21_tax), Decimal("0")).label("tax"),
            session.func.coalesce(session.func.sum(Payslip.net_salary), Decimal("0")).label("net"),
        ).filter(Payslip.payroll_run_id == payroll_run.id).first()

        payroll_run.total_employees = int(row.count) if row else 0
        payroll_run.total_gross = row.gross if row else Decimal("0")
        payroll_run.total_deductions = row.deductions if row else Decimal("0")
        payroll_run.total_tax = row.tax if row else Decimal("0")
        payroll_run.total_net = row.net if row else Decimal("0")
        payroll_run.status = "COMPLETED"
        session.flush()

        logger.info(
            f"Payroll run #{payroll_run.id} finalized: "
            f"{payroll_run.total_employees} employees, total_net={payroll_run.total_net}"
        )

    @staticmethod
    def _build_progress_response(
        payroll_run: PayrollRun, session: Session, batch_size: int
    ) -> dict:
        """Build progress response for batch processing."""
        from app.models.payroll import Payslip

        processed_count = session.query(Payslip).filter(
            Payslip.payroll_run_id == payroll_run.id
        ).count()
        total_count = session.query(Employee).filter(
            Employee.company_id == payroll_run.company_id,
            Employee.is_active == True,
        ).count()

        return {
            "payroll_run_id": payroll_run.id,
            "status": payroll_run.status,
            "processed_count": processed_count,
            "total_count": total_count,
            "batch_size": batch_size,
            "finalized": payroll_run.status == "COMPLETED",
        }

    @staticmethod
    def _process_single_employee(
        emp: EmployeePayrollData,
        payroll_run: PayrollRun,
        config,
        attendance_map: dict,
    ) -> Payslip:
        """Calculate all payroll components for a single employee.

        Args:
            emp: Employee payroll data
            payroll_run: Current payroll run
            config: PayrollConfig with tax/BPJS settings
            attendance_map: Dict of employee_id -> EmployeeAttendanceData

        Returns:
            Built Payslip ORM instance (not yet flushed)
        """
        # 1. Calculate allowances
        allowance_result = calculate_all_allowances(emp.allowances, emp.base_salary)

        # 2. Calculate overtime
        attendance_data = attendance_map.get(emp.employee_id, EmployeeAttendanceData())
        # OT calc uses base + fixed allowances as the salary base
        ot_salary_base = emp.base_salary + allowance_result.total_allowances
        overtime_total = calculate_overtime_total(
            entries=attendance_data.overtime_entries,
            monthly_salary=ot_salary_base,
            work_week_type=config.work_week_type,
        )

        # 3. Gross salary
        gross_salary = (
            emp.base_salary
            + allowance_result.total_allowances
            + overtime_total
            + emp.approved_bonuses
            + emp.reimbursements_taxable
        )

        # 4. BPJS
        bpjs_base = calculate_bpjs_base(emp.base_salary, allowance_result.total_bpjs_base)
        bpjs_result = calculate_all_bpjs(bpjs_base, config.bpjs_settings)

        # 5. PPh 21
        # Taxable gross for tax calculation
        taxable_gross = (
            emp.base_salary
            + allowance_result.total_taxable
            + overtime_total
            + emp.approved_bonuses
            + emp.reimbursements_taxable
        )
        ptkp_annual = config.ptkp_values.get(emp.ptkp_status, Decimal("0"))

        if config.tax_method == "PASAL_17":
            pph21 = calculate_monthly_pph21_pasal17(
                monthly_gross=taxable_gross,
                monthly_bpjs_jht_employee=bpjs_result.jht_employee,
                monthly_bpjs_jp_employee=bpjs_result.jp_employee,
                ptkp_annual=ptkp_annual,
                brackets=config.tax_brackets,
            )
        else:
            # TER method
            category = get_ter_category(emp.ptkp_status)
            ter_rate = find_ter_rate(taxable_gross, category, config.ter_brackets)
            pph21 = calculate_monthly_pph21_ter(taxable_gross, ter_rate)

        # 6. Nett / Gross-up (if applicable)
        tax_allowance = Decimal("0")
        if payroll_run.payroll_method in ("NETT", "GROSS_UP"):
            def tax_calc_fn(g: Decimal) -> Decimal:
                if config.tax_method == "PASAL_17":
                    return calculate_monthly_pph21_pasal17(
                        monthly_gross=g,
                        monthly_bpjs_jht_employee=bpjs_result.jht_employee,
                        monthly_bpjs_jp_employee=bpjs_result.jp_employee,
                        ptkp_annual=ptkp_annual,
                        brackets=config.tax_brackets,
                    )
                else:
                    cat = get_ter_category(emp.ptkp_status)
                    rate = find_ter_rate(g, cat, config.ter_brackets)
                    return calculate_monthly_pph21_ter(g, rate)

            tax_allowance, pph21 = calculate_nett_method_grossup(
                base_gross=taxable_gross,
                tax_calculator_fn=tax_calc_fn,
            )

        # 7. Net salary
        net_salary = calculate_gross_method(
            gross_salary=gross_salary + tax_allowance,
            pph21_tax=pph21,
            bpjs_employee_total=bpjs_result.total_employee,
            kasbon_deduction=emp.kasbon_due,
            other_deductions=Decimal("0"),
        )

        # 8. Build payslip
        payslip = PayslipBuilder.build_payslip(
            payroll_run_id=payroll_run.id,
            employee_data=emp,
            payroll_period=payroll_run.payroll_period,
            allowance_result=allowance_result,
            overtime_total=overtime_total,
            bpjs_result=bpjs_result,
            pph21_tax=pph21,
            tax_allowance=tax_allowance,
            net_salary=net_salary,
            gross_salary=gross_salary,
            attendance_data=attendance_data,
            kasbon_deduction=emp.kasbon_due,
            other_deductions=Decimal("0"),
        )

        return payslip

    @staticmethod
    def approve_payroll_run(
        payroll_run_id: int,
        approved_by: int,
        session: Session,
    ) -> PayrollRun:
        """Approve a completed payroll run.

        Steps:
        1. Validate status == COMPLETED
        2. Set status = APPROVED, approved_by, approval_date
        3. Mark all payslips as approved

        Args:
            payroll_run_id: PayrollRun ID to approve
            approved_by: User ID of approver
            session: SQLAlchemy session

        Returns:
            Updated PayrollRun with APPROVED status

        Raises:
            PayrollValidationError: If run is not in COMPLETED status
        """
        payroll_run = session.query(PayrollRun).filter(
            PayrollRun.id == payroll_run_id
        ).first()
        if not payroll_run:
            raise PayrollRunError(
                f"Payroll run not found: {payroll_run_id}",
                {"payroll_run_id": payroll_run_id},
            )

        if payroll_run.status != "COMPLETED":
            raise PayrollValidationError(
                f"Payroll run must be in COMPLETED status to approve. Current: {payroll_run.status}",
                {"payroll_run_id": payroll_run_id, "current_status": payroll_run.status},
            )

        payroll_run.status = "APPROVED"
        payroll_run.approved_by = approved_by
        payroll_run.approval_date = datetime.utcnow()

        # Mark all payslips as approved
        session.query(Payslip).filter(
            Payslip.payroll_run_id == payroll_run_id
        ).update({"is_approved": True})

        session.flush()

        logger.info(
            f"Payroll run #{payroll_run_id} approved by user {approved_by}"
        )

        return payroll_run

    @staticmethod
    def get_payroll_run(payroll_run_id: int, session: Session) -> Optional[PayrollRun]:
        """Get payroll run with payslips.

        Args:
            payroll_run_id: PayrollRun ID
            session: SQLAlchemy session

        Returns:
            PayrollRun with eagerly loaded payslips, or None if not found
        """
        from sqlalchemy.orm import selectinload

        return session.query(PayrollRun).options(
            selectinload(PayrollRun.payslips)
        ).filter(
            PayrollRun.id == payroll_run_id
        ).first()

    @staticmethod
    def list_payroll_runs(
        company_id: int,
        session: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> List[PayrollRun]:
        """List payroll runs for a company.

        Args:
            company_id: Company ID to filter by
            session: SQLAlchemy session
            skip: Number of records to skip (offset)
            limit: Maximum records to return

        Returns:
            List of PayrollRun instances ordered by period descending
        """
        return session.query(PayrollRun).filter(
            PayrollRun.company_id == company_id
        ).order_by(
            PayrollRun.payroll_period.desc()
        ).offset(skip).limit(limit).all()
