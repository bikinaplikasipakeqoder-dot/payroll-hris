"""
Attendance and Overtime API endpoints.
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.attendance import AttendanceRecord, OvertimeRecord
from app.models.employee import Employee
from app.schemas.attendance import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceSummaryResponse,
    OvertimeApprovalRequest,
    OvertimeRecordCreate,
    OvertimeRecordResponse,
)

router = APIRouter(prefix="/attendance", tags=["Attendance & Overtime"])


# --- Attendance Endpoints ---


@router.post(
    "",
    response_model=AttendanceRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record attendance entry",
)
def create_attendance(
    payload: AttendanceRecordCreate,
    db: Session = Depends(get_db),
):
    """Record a daily attendance entry for an employee."""
    # Check for duplicate attendance on same date
    existing = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.employee_id == payload.employee_id,
            AttendanceRecord.attendance_date == payload.attendance_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DuplicateAttendance",
                "message": f"Attendance record already exists for employee {payload.employee_id} on {payload.attendance_date}",
            },
        )

    record = AttendanceRecord(
        employee_id=payload.employee_id,
        attendance_date=payload.attendance_date,
        status=payload.status,
        check_in_time=payload.check_in_time,
        check_out_time=payload.check_out_time,
        is_late=False,
        late_minutes=0,
        notes=payload.notes,
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get(
    "",
    response_model=List[AttendanceRecordResponse],
    summary="List attendance records",
)
def list_attendance(
    employee_id: Optional[int] = Query(None, description="Employee ID"),
    company_id: Optional[int] = Query(None, description="Company ID (admin view)"),
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List attendance records for an employee or company with optional date range filter."""
    query = db.query(AttendanceRecord)

    if employee_id is not None:
        query = query.filter(AttendanceRecord.employee_id == employee_id)
    elif company_id is not None:
        query = query.join(Employee, AttendanceRecord.employee_id == Employee.id).filter(
            Employee.company_id == company_id
        )

    if date_from is not None:
        query = query.filter(AttendanceRecord.attendance_date >= date_from)
    if date_to is not None:
        query = query.filter(AttendanceRecord.attendance_date <= date_to)

    records = (
        query.order_by(AttendanceRecord.attendance_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records


@router.get(
    "/summary",
    response_model=List[AttendanceSummaryResponse],
    summary="Monthly attendance summary by employee",
)
def attendance_summary(
    company_id: int = Query(..., description="Company ID"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    db: Session = Depends(get_db),
):
    """Return monthly attendance summary per active employee.

    Total working days are calculated as weekdays (Mon-Fri) in the month.
    """
    from calendar import monthrange

    employees = (
        db.query(Employee.id, Employee.employee_code, Employee.full_name)
        .filter(Employee.company_id == company_id, Employee.is_active == True)
        .all()
    )

    _, last_day = monthrange(year, month)
    period_start = date(year, month, 1)
    period_end = date(year, month, last_day)

    # Count weekdays in the month as total working days
    total_working_days = 0
    for day in range(1, last_day + 1):
        weekday = date(year, month, day).weekday()
        if weekday < 5:  # Monday=0 ... Friday=4
            total_working_days += 1

    records = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.employee_id.in_([e.id for e in employees]),
            AttendanceRecord.attendance_date >= period_start,
            AttendanceRecord.attendance_date <= period_end,
        )
        .all()
    )

    # Group records by employee_id
    grouped: Dict[int, List[AttendanceRecord]] = {}
    for rec in records:
        grouped.setdefault(rec.employee_id, []).append(rec)

    result = []
    for emp in employees:
        emp_records = grouped.get(emp.id, [])
        present_days = 0
        absent_days = 0
        sick_days = 0
        leave_days = 0
        permitted_days = 0
        late_minutes = 0

        for rec in emp_records:
            if rec.status == "PRESENT":
                present_days += 1
                if rec.late_minutes:
                    late_minutes += rec.late_minutes
            elif rec.status == "ABSENT":
                absent_days += 1
            elif rec.status == "SICK":
                sick_days += 1
            elif rec.status == "LEAVE":
                leave_days += 1
            elif rec.status == "PERMITTED":
                permitted_days += 1

        attendance_days = present_days + leave_days + permitted_days + sick_days
        percentage = (attendance_days / total_working_days * 100) if total_working_days > 0 else 0.0

        result.append(
            AttendanceSummaryResponse(
                employee_id=emp.id,
                employee_code=emp.employee_code,
                employee_name=emp.full_name,
                total_working_days=total_working_days,
                present_days=present_days,
                absent_days=absent_days,
                sick_days=sick_days,
                leave_days=leave_days,
                permitted_days=permitted_days,
                late_minutes=late_minutes,
                attendance_percentage=round(percentage, 2),
            )
        )

    return result


@router.post(
    "/clock-in",
    response_model=AttendanceRecordResponse,
    summary="Employee clock-in",
)
def clock_in(
    employee_id: int = Query(..., description="Employee ID"),
    db: Session = Depends(get_db),
):
    """Record employee clock-in for today. Creates record if not exists."""
    today = date.today()
    now = datetime.now().strftime("%H:%M:%S")

    record = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.attendance_date == today,
        )
        .first()
    )

    if record and record.check_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "AlreadyClockedIn", "message": "Employee already clocked in today"},
        )

    if record:
        record.check_in_time = now
        record.status = "PRESENT"
    else:
        record = AttendanceRecord(
            employee_id=employee_id,
            attendance_date=today,
            status="PRESENT",
            check_in_time=now,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/clock-out",
    response_model=AttendanceRecordResponse,
    summary="Employee clock-out",
)
def clock_out(
    employee_id: int = Query(..., description="Employee ID"),
    db: Session = Depends(get_db),
):
    """Record employee clock-out for today. Requires clock-in first."""
    today = date.today()
    now = datetime.now().strftime("%H:%M:%S")

    record = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.attendance_date == today,
        )
        .first()
    )

    if not record or not record.check_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "NotClockedIn", "message": "Employee has not clocked in today"},
        )

    if record.check_out_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "AlreadyClockedOut", "message": "Employee already clocked out today"},
        )

    record.check_out_time = now
    db.commit()
    db.refresh(record)
    return record


# --- Overtime Endpoints ---


@router.post(
    "/overtime",
    response_model=OvertimeRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record overtime entry",
)
def create_overtime(
    payload: OvertimeRecordCreate,
    db: Session = Depends(get_db),
):
    """Record an overtime work entry for an employee."""
    record = OvertimeRecord(
        employee_id=payload.employee_id,
        overtime_date=payload.overtime_date,
        overtime_type=payload.overtime_type,
        hours=payload.hours,
        multiplier=1.5,  # Default multiplier; actual calculation during payroll
        approval_status="PENDING",
        notes=payload.notes,
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get(
    "/overtime",
    response_model=List[OvertimeRecordResponse],
    summary="List overtime records",
)
def list_overtime(
    employee_id: int = Query(..., description="Employee ID"),
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List overtime records for an employee with optional filters."""
    query = db.query(OvertimeRecord).filter(
        OvertimeRecord.employee_id == employee_id
    )

    if date_from is not None:
        query = query.filter(OvertimeRecord.overtime_date >= date_from)
    if date_to is not None:
        query = query.filter(OvertimeRecord.overtime_date <= date_to)
    if approval_status is not None:
        query = query.filter(OvertimeRecord.approval_status == approval_status)

    records = (
        query.order_by(OvertimeRecord.overtime_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records


@router.patch(
    "/overtime/{overtime_id}/approve",
    response_model=OvertimeRecordResponse,
    summary="Approve or reject overtime",
)
def approve_overtime(
    overtime_id: int,
    payload: OvertimeApprovalRequest,
    db: Session = Depends(get_db),
):
    """Approve or reject an overtime record."""
    record = db.query(OvertimeRecord).filter(OvertimeRecord.id == overtime_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Overtime record {overtime_id} not found"},
        )

    if record.approval_status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "InvalidState",
                "message": f"Overtime record is already {record.approval_status}",
            },
        )

    record.approval_status = payload.approval_status
    record.approved_by = payload.approved_by
    record.approval_date = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record
