"""
Master/reference data CRUD API endpoints.

Covers: Departments, Positions, Grades, Employment Statuses.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Department, Position, EmploymentStatus, Employee
from app.models.salary import Grade
from app.schemas.master_data import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    PositionCreate, PositionUpdate, PositionResponse,
    GradeCreate, GradeUpdate, GradeResponse,
    EmploymentStatusCreate, EmploymentStatusUpdate, EmploymentStatusResponse,
)

router = APIRouter(prefix="/master-data", tags=["Master Data"])


# ─── Department Endpoints ─────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentResponse], summary="List departments")
def list_departments(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all departments for a company."""
    return db.query(Department).filter(Department.company_id == company_id).all()


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    """Create a new department."""
    department = Department(
        company_id=payload.company_id,
        code=payload.code,
        name=payload.name,
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.patch("/departments/{department_id}", response_model=DepartmentResponse, summary="Update department")
def update_department(department_id: int, payload: DepartmentUpdate, db: Session = Depends(get_db)):
    """Partially update a department."""
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Department {department_id} not found"},
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(department, field, value)
    db.commit()
    db.refresh(department)
    return department


@router.delete("/departments/{department_id}", status_code=status.HTTP_200_OK, summary="Delete department")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    """Delete a department. Fails if employees are assigned to it."""
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Department {department_id} not found"},
        )
    count = db.query(Employee).filter(Employee.department_id == department_id).count()
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InUse", "message": f"Cannot delete: {count} employees are assigned to this department."},
        )
    db.delete(department)
    db.commit()
    return {"message": "Department deleted"}


# ─── Position Endpoints ───────────────────────────────────────────────────────

@router.get("/positions", response_model=List[PositionResponse], summary="List positions")
def list_positions(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all positions for a company."""
    return db.query(Position).filter(Position.company_id == company_id).all()


@router.post(
    "/positions",
    response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create position",
)
def create_position(payload: PositionCreate, db: Session = Depends(get_db)):
    """Create a new position."""
    position = Position(
        company_id=payload.company_id,
        code=payload.code,
        name=payload.name,
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


@router.patch("/positions/{position_id}", response_model=PositionResponse, summary="Update position")
def update_position(position_id: int, payload: PositionUpdate, db: Session = Depends(get_db)):
    """Partially update a position."""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Position {position_id} not found"},
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(position, field, value)
    db.commit()
    db.refresh(position)
    return position


@router.delete("/positions/{position_id}", status_code=status.HTTP_200_OK, summary="Delete position")
def delete_position(position_id: int, db: Session = Depends(get_db)):
    """Delete a position. Fails if employees are assigned to it."""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Position {position_id} not found"},
        )
    count = db.query(Employee).filter(Employee.position_id == position_id).count()
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InUse", "message": f"Cannot delete: {count} employees are assigned to this position."},
        )
    db.delete(position)
    db.commit()
    return {"message": "Position deleted"}


# ─── Grade Endpoints ──────────────────────────────────────────────────────────

@router.get("/grades", response_model=List[GradeResponse], summary="List grades")
def list_grades(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all grades for a company."""
    return db.query(Grade).filter(Grade.company_id == company_id).all()


@router.post(
    "/grades",
    response_model=GradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create grade",
)
def create_grade(payload: GradeCreate, db: Session = Depends(get_db)):
    """Create a new grade."""
    grade = Grade(
        company_id=payload.company_id,
        grade_code=payload.grade_code,
        grade_name=payload.grade_name,
    )
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return grade


@router.patch("/grades/{grade_id}", response_model=GradeResponse, summary="Update grade")
def update_grade(grade_id: int, payload: GradeUpdate, db: Session = Depends(get_db)):
    """Partially update a grade."""
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Grade {grade_id} not found"},
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(grade, field, value)
    db.commit()
    db.refresh(grade)
    return grade


@router.delete("/grades/{grade_id}", status_code=status.HTTP_200_OK, summary="Delete grade")
def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    """Delete a grade. Fails if employees are assigned to it."""
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Grade {grade_id} not found"},
        )
    count = db.query(Employee).filter(Employee.grade_id == grade_id).count()
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InUse", "message": f"Cannot delete: {count} employees are assigned to this grade."},
        )
    db.delete(grade)
    db.commit()
    return {"message": "Grade deleted"}


# ─── Employment Status Endpoints ─────────────────────────────────────────────

@router.get("/employment-statuses", response_model=List[EmploymentStatusResponse], summary="List employment statuses")
def list_employment_statuses(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all employment statuses for a company."""
    return db.query(EmploymentStatus).filter(EmploymentStatus.company_id == company_id).all()


@router.post(
    "/employment-statuses",
    response_model=EmploymentStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employment status",
)
def create_employment_status(payload: EmploymentStatusCreate, db: Session = Depends(get_db)):
    """Create a new employment status."""
    emp_status = EmploymentStatus(
        company_id=payload.company_id,
        name=payload.name,
        code=payload.code,
    )
    db.add(emp_status)
    db.commit()
    db.refresh(emp_status)
    return emp_status


@router.patch("/employment-statuses/{status_id}", response_model=EmploymentStatusResponse, summary="Update employment status")
def update_employment_status(status_id: int, payload: EmploymentStatusUpdate, db: Session = Depends(get_db)):
    """Partially update an employment status."""
    emp_status = db.query(EmploymentStatus).filter(EmploymentStatus.id == status_id).first()
    if not emp_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Employment status {status_id} not found"},
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(emp_status, field, value)
    db.commit()
    db.refresh(emp_status)
    return emp_status


@router.delete("/employment-statuses/{status_id}", status_code=status.HTTP_200_OK, summary="Delete employment status")
def delete_employment_status(status_id: int, db: Session = Depends(get_db)):
    """Delete an employment status. Fails if employees are assigned to it."""
    emp_status = db.query(EmploymentStatus).filter(EmploymentStatus.id == status_id).first()
    if not emp_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Employment status {status_id} not found"},
        )
    count = db.query(Employee).filter(Employee.employment_status_id == status_id).count()
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InUse", "message": f"Cannot delete: {count} employees are assigned to this employment status."},
        )
    db.delete(emp_status)
    db.commit()
    return {"message": "Employment status deleted"}
