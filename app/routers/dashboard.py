"""
Dashboard aggregation endpoints.
Provides high-level statistics for the main dashboard UI.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.employee import Employee, Department
from app.models.attendance import OvertimeRecord
from app.models.payroll import PayrollRun

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", summary="Get dashboard statistics")
def get_dashboard_stats(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """Return aggregated statistics for the dashboard."""
    # Total active employees
    total_employees = db.query(Employee).filter(
        Employee.company_id == company_id,
        Employee.is_active == True,
    ).count()

    # Employees by department
    dept_rows = (
        db.query(Department.name, func.count(Employee.id).label("count"))
        .join(Employee, Employee.department_id == Department.id)
        .filter(
            Department.company_id == company_id,
            Employee.is_active == True,
        )
        .group_by(Department.name)
        .all()
    )
    employees_by_department = [
        {"department": name or "Belum ada departemen", "count": count}
        for name, count in dept_rows
    ]

    # Active payroll runs (not yet paid/approved)
    active_payroll_runs = db.query(PayrollRun).filter(
        PayrollRun.company_id == company_id,
        PayrollRun.status.in_(["DRAFT", "PROCESSING", "COMPLETED"]),
    ).count()

    # Pending overtime approvals (join via employee)
    pending_overtime = (
        db.query(OvertimeRecord)
        .join(Employee, OvertimeRecord.employee_id == Employee.id)
        .filter(
            Employee.company_id == company_id,
            OvertimeRecord.approval_status == "PENDING",
        )
        .count()
    )

    # Monthly payroll trend (last 6 completed runs)
    payroll_runs = (
        db.query(PayrollRun)
        .filter(
            PayrollRun.company_id == company_id,
            PayrollRun.status == "COMPLETED",
        )
        .order_by(PayrollRun.payroll_period.desc())
        .limit(6)
        .all()
    )
    monthly_trend = [
        {
            "period": run.payroll_period,
            "month": _month_label(run.payroll_period),
            "amount": float(run.total_net or 0),
        }
        for run in reversed(payroll_runs)
    ]

    # Total payroll for current month
    current_period = date.today().strftime("%Y-%m")
    current_run = (
        db.query(PayrollRun)
        .filter(
            PayrollRun.company_id == company_id,
            PayrollRun.payroll_period == current_period,
            PayrollRun.status == "COMPLETED",
        )
        .first()
    )
    total_payroll_this_month = float(current_run.total_net) if current_run else 0

    return {
        "total_employees": total_employees,
        "employees_by_department": employees_by_department,
        "active_payroll_runs": active_payroll_runs,
        "pending_overtime": pending_overtime,
        "total_payroll_this_month": total_payroll_this_month,
        "monthly_trend": monthly_trend,
    }


def _month_label(payroll_period: str) -> str:
    """Convert YYYY-MM to Indonesian month abbreviation."""
    month_map = {
        "01": "Jan",
        "02": "Feb",
        "03": "Mar",
        "04": "Apr",
        "05": "Mei",
        "06": "Jun",
        "07": "Jul",
        "08": "Agu",
        "09": "Sep",
        "10": "Okt",
        "11": "Nov",
        "12": "Des",
    }
    _, month = payroll_period.split("-")
    return month_map.get(month, month)
