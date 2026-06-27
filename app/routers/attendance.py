"""
Attendance and Overtime API endpoints.
"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.attendance import AttendanceRecord, OvertimeRecord
from app.models.employee import Employee
from app.schemas.attendance import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
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
