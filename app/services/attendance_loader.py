"""
Attendance and overtime data loader.
Loads all records for a payroll period and groups by employee_id for O(1) lookup.
"""
from decimal import Decimal
from datetime import date
from typing import List, Dict
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord, OvertimeRecord
from app.utils.decimal_utils import to_decimal
from app.calculations.overtime import OvertimeEntry


@dataclass
class AttendanceSummary:
    """Attendance summary for an employee in a period."""
    working_days: int = 0
    present_days: int = 0
    absent_days: int = 0
    late_minutes: int = 0
    sick_days: int = 0
    leave_days: int = 0


@dataclass
class EmployeeAttendanceData:
    """All attendance and overtime data for one employee."""
    summary: AttendanceSummary = field(default_factory=AttendanceSummary)
    overtime_entries: List[OvertimeEntry] = field(default_factory=list)
    total_overtime_hours: Decimal = Decimal("0")


class AttendanceLoader:
    """Loads attendance and overtime records for a payroll period."""

    @staticmethod
    def load_period(
        company_id: int,
        employee_ids: List[int],
        period_start: date,
        period_end: date,
        session: Session,
    ) -> Dict[int, EmployeeAttendanceData]:
        """Load attendance and overtime records, grouped by employee_id.

        Returns dict mapping employee_id -> EmployeeAttendanceData
        """
        if not employee_ids:
            return {}

        # Load attendance records for all employees in period
        attendance_records = session.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id.in_(employee_ids),
            AttendanceRecord.attendance_date >= period_start,
            AttendanceRecord.attendance_date <= period_end,
        ).all()

        # Load approved overtime records
        overtime_records = session.query(OvertimeRecord).filter(
            OvertimeRecord.employee_id.in_(employee_ids),
            OvertimeRecord.overtime_date >= period_start,
            OvertimeRecord.overtime_date <= period_end,
            OvertimeRecord.approval_status == "APPROVED",
        ).all()

        # Group by employee
        result: Dict[int, EmployeeAttendanceData] = {}

        # Process attendance
        for rec in attendance_records:
            if rec.employee_id not in result:
                result[rec.employee_id] = EmployeeAttendanceData()

            data = result[rec.employee_id]
            data.summary.working_days += 1

            if rec.status == "PRESENT":
                data.summary.present_days += 1
                if rec.late_minutes:
                    data.summary.late_minutes += rec.late_minutes
            elif rec.status == "ABSENT":
                data.summary.absent_days += 1
            elif rec.status == "SICK":
                data.summary.sick_days += 1
            elif rec.status == "LEAVE":
                data.summary.leave_days += 1

        # Process overtime
        for ot in overtime_records:
            if ot.employee_id not in result:
                result[ot.employee_id] = EmployeeAttendanceData()

            data = result[ot.employee_id]
            hours = to_decimal(ot.hours)
            data.overtime_entries.append(OvertimeEntry(
                overtime_type=ot.overtime_type,
                hours=hours,
            ))
            data.total_overtime_hours += hours

        return result
