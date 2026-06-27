"""
Employee CRUD API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.payroll import Payslip
from app.models.salary import AllowanceType, EmployeeAllowance
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.schemas.payroll import PayslipResponse
from app.schemas.salary import (
    EmployeeAllowanceCreate,
    EmployeeAllowanceResponse,
    EmployeeAllowanceUpdate,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get(
    "",
    response_model=List[EmployeeResponse],
    summary="List employees",
)
def list_employees(
    company_id: int = Query(..., description="Company ID"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List employees with optional filters and pagination."""
    query = db.query(Employee).filter(Employee.company_id == company_id)

    if department_id is not None:
        query = query.filter(Employee.department_id == department_id)
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)

    employees = query.offset(skip).limit(limit).all()
    return employees


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    """Create a new employee record. Employee code must be unique per company."""
    # Check unique employee_code within company
    existing = (
        db.query(Employee)
        .filter(
            Employee.company_id == payload.company_id,
            Employee.employee_code == payload.employee_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DuplicateEmployee",
                "message": f"Employee code '{payload.employee_code}' already exists for this company",
            },
        )

    # Build full_name
    full_name = payload.first_name
    if payload.last_name:
        full_name = f"{payload.first_name} {payload.last_name}"

    employee = Employee(
        company_id=payload.company_id,
        employee_code=payload.employee_code,
        first_name=payload.first_name,
        last_name=payload.last_name,
        full_name=full_name,
        personal_id_number=payload.personal_id_number,
        npwp=payload.npwp_number,
        ptkp_status=payload.ptkp_status,
        religion=payload.religion,
        gender=payload.gender,
        date_of_birth=payload.date_of_birth,
        date_joined=payload.date_joined,
        department_id=payload.department_id,
        position_id=payload.position_id,
        grade_id=payload.grade_id,
        employment_status_id=payload.employment_status_id,
        base_salary=payload.base_salary,
        bank_name=payload.bank_name,
        bank_account_number=payload.bank_account_number,
        bank_account_holder_name=payload.bank_account_name,
        bpjs_kesehatan_number=payload.bpjs_kes_number,
        bpjs_ketenagakerjaan_number=payload.bpjs_tk_number,
        phone=payload.phone,
        email=payload.email,
        address_street=payload.address_street,
        address_city=payload.address_city,
        address_province=payload.address_province,
        address_postal_code=payload.address_postal_code,
        is_active=True,
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee detail",
)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """Retrieve a single employee by ID."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Employee {employee_id} not found"},
        )
    return employee


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee (partial)",
)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    """Partially update an employee — only provided fields are applied."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Employee {employee_id} not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Map schema field names to model field names where they differ
    field_mapping = {
        "npwp_number": "npwp",
        "bank_account_name": "bank_account_holder_name",
        "bpjs_kes_number": "bpjs_kesehatan_number",
        "bpjs_tk_number": "bpjs_ketenagakerjaan_number",
    }

    for field, value in update_data.items():
        model_field = field_mapping.get(field, field)
        setattr(employee, model_field, value)

    # Recompute full_name if name fields changed
    if "first_name" in update_data or "last_name" in update_data:
        first = employee.first_name
        last = employee.last_name
        employee.full_name = f"{first} {last}" if last else first

    db.commit()
    db.refresh(employee)
    return employee


@router.delete(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Deactivate employee (soft delete)",
)
def deactivate_employee(employee_id: int, db: Session = Depends(get_db)):
    """Soft-delete an employee by setting is_active=False."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Employee {employee_id} not found"},
        )

    employee.is_active = False
    db.commit()
    db.refresh(employee)
    return employee


# ─── Employee Allowances ──────────────────────────────────────────────────────


@router.get(
    "/{employee_id}/allowances",
    response_model=List[EmployeeAllowanceResponse],
    summary="List employee allowances",
)
def list_employee_allowances(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """List all allowance assignments for an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Employee {employee_id} not found"},
        )

    allowances = (
        db.query(EmployeeAllowance)
        .filter(EmployeeAllowance.employee_id == employee_id)
        .order_by(EmployeeAllowance.effective_date.desc())
        .all()
    )

    return [
        {
            **allowance.__dict__,
            "allowance_type_name": allowance.allowance_type.name,
            "allowance_type_code": allowance.allowance_type.code,
        }
        for allowance in allowances
    ]


@router.post(
    "/{employee_id}/allowances",
    response_model=EmployeeAllowanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee allowance",
)
def create_employee_allowance(
    employee_id: int,
    payload: EmployeeAllowanceCreate,
    db: Session = Depends(get_db),
):
    """Assign a new allowance to an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Employee {employee_id} not found"},
        )

    allowance_type = db.query(AllowanceType).filter(
        AllowanceType.id == payload.allowance_type_id,
        AllowanceType.company_id == employee.company_id,
    ).first()
    if not allowance_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": "Allowance type not found for this company",
            },
        )

    existing = (
        db.query(EmployeeAllowance)
        .filter(
            EmployeeAllowance.employee_id == employee_id,
            EmployeeAllowance.allowance_type_id == payload.allowance_type_id,
            EmployeeAllowance.effective_date == payload.effective_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Duplicate",
                "message": "Allowance already exists for this employee and effective date",
            },
        )

    allowance = EmployeeAllowance(
        employee_id=employee_id,
        allowance_type_id=payload.allowance_type_id,
        amount=payload.amount,
        effective_date=payload.effective_date,
        end_date=payload.end_date,
        notes=payload.notes,
        is_active=payload.is_active,
    )
    db.add(allowance)
    db.commit()
    db.refresh(allowance)

    return {
        **allowance.__dict__,
        "allowance_type_name": allowance.allowance_type.name,
        "allowance_type_code": allowance.allowance_type.code,
    }


@router.patch(
    "/{employee_id}/allowances/{allowance_id}",
    response_model=EmployeeAllowanceResponse,
    summary="Update employee allowance",
)
def update_employee_allowance(
    employee_id: int,
    allowance_id: int,
    payload: EmployeeAllowanceUpdate,
    db: Session = Depends(get_db),
):
    """Partially update an employee allowance assignment."""
    allowance = (
        db.query(EmployeeAllowance)
        .filter(
            EmployeeAllowance.id == allowance_id,
            EmployeeAllowance.employee_id == employee_id,
        )
        .first()
    )
    if not allowance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Employee allowance not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "allowance_type_id" in update_data:
        allowance_type = db.query(AllowanceType).filter(
            AllowanceType.id == update_data["allowance_type_id"],
            AllowanceType.company_id == allowance.employee.company_id,
        ).first()
        if not allowance_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": "Allowance type not found for this company",
                },
            )

    if "allowance_type_id" in update_data or "effective_date" in update_data:
        existing = (
            db.query(EmployeeAllowance)
            .filter(
                EmployeeAllowance.employee_id == employee_id,
                EmployeeAllowance.allowance_type_id == update_data.get(
                    "allowance_type_id", allowance.allowance_type_id
                ),
                EmployeeAllowance.effective_date == update_data.get(
                    "effective_date", allowance.effective_date
                ),
                EmployeeAllowance.id != allowance_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Duplicate",
                    "message": "Allowance already exists for this employee and effective date",
                },
            )

    for field, value in update_data.items():
        setattr(allowance, field, value)

    db.commit()
    db.refresh(allowance)

    return {
        **allowance.__dict__,
        "allowance_type_name": allowance.allowance_type.name,
        "allowance_type_code": allowance.allowance_type.code,
    }


@router.delete(
    "/{employee_id}/allowances/{allowance_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete employee allowance",
)
def delete_employee_allowance(
    employee_id: int,
    allowance_id: int,
    db: Session = Depends(get_db),
):
    """Delete an employee allowance assignment."""
    allowance = (
        db.query(EmployeeAllowance)
        .filter(
            EmployeeAllowance.id == allowance_id,
            EmployeeAllowance.employee_id == employee_id,
        )
        .first()
    )
    if not allowance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Employee allowance not found"},
        )

    db.delete(allowance)
    db.commit()
    return {"message": "Employee allowance deleted"}


# ─── Employee Self-Service ───────────────────────────────────────────────────


@router.get(
    "/{employee_id}/profile",
    response_model=EmployeeResponse,
    summary="Get employee profile (self-service)",
)
def get_employee_profile(employee_id: int, db: Session = Depends(get_db)):
    """Retrieve full employee profile for self-service portal."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Employee not found"},
        )
    return employee


@router.get(
    "/{employee_id}/payslips",
    response_model=List[PayslipResponse],
    summary="Get employee payslip history (self-service)",
)
def get_employee_payslips(
    employee_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve payslip history for an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Employee not found"},
        )

    payslips = (
        db.query(Payslip)
        .filter(Payslip.employee_id == employee_id)
        .order_by(Payslip.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return payslips
