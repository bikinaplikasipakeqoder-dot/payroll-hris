"""
Employee CRUD API endpoints.
"""

from typing import List, Optional
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from decimal import Decimal

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.models.company_entity import Entity, UmpSetting
from app.models.employee import Employee
from app.models.payroll import Payslip
from app.models.salary import AllowanceType, EmployeeAllowance, EmployeeSalaryHistory
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    EmployeeListResponse,
)
from app.schemas.payroll import PayslipResponse
from app.schemas.salary import (
    EmployeeAllowanceCreate,
    EmployeeAllowanceResponse,
    EmployeeAllowanceUpdate,
    EmployeeSalaryHistoryCreate,
    EmployeeSalaryHistoryResponse,
    EmployeeSalaryHistoryUpdate,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


def _get_ump_amount(db: Session, company_id: int, province: Optional[str], city: Optional[str]) -> Optional[Decimal]:
    """Fetch the active UMP amount for a province/city, preferring city-specific over province-only."""
    if not province:
        return None

    query = db.query(UmpSetting).filter(
        UmpSetting.company_id == company_id,
        UmpSetting.province.ilike(province.strip()),
        UmpSetting.is_active == True,
    )
    if city:
        city_match = query.filter(UmpSetting.city.ilike(city.strip())).order_by(UmpSetting.effective_date.desc()).first()
        if city_match:
            return city_match.amount

    province_match = query.filter(UmpSetting.city.is_(None)).order_by(UmpSetting.effective_date.desc()).first()
    if province_match:
        return province_match.amount

    return None


def _get_latest_base_salary(
    db: Session,
    employee_id: int,
    as_of_date: Optional[date] = None,
) -> Optional[EmployeeSalaryHistory]:
    """Return the most recent active base salary record for an employee as of a date."""
    query = db.query(EmployeeSalaryHistory).filter(
        EmployeeSalaryHistory.employee_id == employee_id,
        EmployeeSalaryHistory.is_active == True,
    )
    if as_of_date:
        query = query.filter(EmployeeSalaryHistory.effective_date <= as_of_date)
        query = query.filter(
            (EmployeeSalaryHistory.end_date.is_(None)) | (EmployeeSalaryHistory.end_date >= as_of_date)
        )
    return query.order_by(EmployeeSalaryHistory.effective_date.desc()).first()


def _attach_current_base_salary(employee: Employee, db: Session) -> None:
    """Attach current base salary and effective date from history to employee object."""
    record = _get_latest_base_salary(db, employee.id)
    employee.base_salary = record.base_salary if record else None
    employee.base_salary_effective_date = record.effective_date if record else None


def _attach_current_base_salary_batch(employees: List[Employee], db: Session) -> None:
    """Attach current base salary for a list of employees using a single query."""
    if not employees:
        return

    employee_ids = [emp.id for emp in employees]

    # Subquery: latest effective_date per employee among active records.
    latest_subq = (
        db.query(
            EmployeeSalaryHistory.employee_id,
            func.max(EmployeeSalaryHistory.effective_date).label("max_date"),
        )
        .filter(
            EmployeeSalaryHistory.employee_id.in_(employee_ids),
            EmployeeSalaryHistory.is_active == True,
        )
        .group_by(EmployeeSalaryHistory.employee_id)
        .subquery()
    )

    # Fetch the actual records matching the latest effective_date.
    latest_records = (
        db.query(EmployeeSalaryHistory)
        .join(
            latest_subq,
            and_(
                EmployeeSalaryHistory.employee_id == latest_subq.c.employee_id,
                EmployeeSalaryHistory.effective_date == latest_subq.c.max_date,
            ),
        )
        .filter(EmployeeSalaryHistory.is_active == True)
        .all()
    )

    salary_map = {record.employee_id: record for record in latest_records}
    for emp in employees:
        record = salary_map.get(emp.id)
        emp.base_salary = record.base_salary if record else None
        emp.base_salary_effective_date = record.effective_date if record else None


def _set_base_salary(
    db: Session,
    employee_id: int,
    base_salary: Decimal,
    effective_date: Optional[date] = None,
    notes: Optional[str] = None,
    user_id: Optional[int] = None,
) -> None:
    """Create a new salary history record and close the previous active record."""
    effective = effective_date or date.today()

    # Close the currently active record if its effective_date is before the new one
    active_record = (
        db.query(EmployeeSalaryHistory)
        .filter(
            EmployeeSalaryHistory.employee_id == employee_id,
            EmployeeSalaryHistory.is_active == True,
            EmployeeSalaryHistory.effective_date < effective,
            EmployeeSalaryHistory.end_date.is_(None),
        )
        .order_by(EmployeeSalaryHistory.effective_date.desc())
        .first()
    )
    if active_record:
        # Set end_date to one day before the new effective date
        active_record.end_date = effective - timedelta(days=1)

    # If a record already exists with the same effective_date, update it
    same_date_record = (
        db.query(EmployeeSalaryHistory)
        .filter(
            EmployeeSalaryHistory.employee_id == employee_id,
            EmployeeSalaryHistory.effective_date == effective,
        )
        .first()
    )
    if same_date_record:
        same_date_record.base_salary = base_salary
        same_date_record.notes = notes or same_date_record.notes
        same_date_record.is_active = True
        same_date_record.end_date = None
        same_date_record.updated_by = user_id
    else:
        new_record = EmployeeSalaryHistory(
            employee_id=employee_id,
            base_salary=base_salary,
            effective_date=effective,
            notes=notes,
            is_active=True,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(new_record)

    # Sync the employee cache column to the latest active salary
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if employee:
        employee.base_salary = base_salary


def _validate_ump(
    db: Session,
    company_id: int,
    entity_id: Optional[int],
    base_salary: Optional[Decimal],
) -> None:
    """Validate base salary is not below the UMP for the entity location."""
    if base_salary is None:
        return

    province = None
    city = None
    if entity_id:
        entity = db.query(Entity).filter(Entity.id == entity_id, Entity.company_id == company_id).first()
        if entity:
            province = entity.province
            city = entity.city

    ump = _get_ump_amount(db, company_id, province, city)
    if ump is not None and base_salary < ump:
        location = f"{city}, {province}" if city else province
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "BelowUmp",
                "message": f"Gaji pokok (Rp {base_salary:,.0f}) di bawah UMP {location} (Rp {ump:,.0f})",
            },
        )


@router.get(
    "",
    response_model=EmployeeListResponse,
    summary="List employees",
)
def list_employees(
    company_id: int = Query(..., description="Company ID"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by full name or employee code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List employees with optional filters, search, and pagination."""
    query = db.query(Employee).filter(Employee.company_id == company_id)

    if department_id is not None:
        query = query.filter(Employee.department_id == department_id)
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Employee.full_name.ilike(pattern))
            | (Employee.employee_code.ilike(pattern))
            | (Employee.first_name.ilike(pattern))
            | (Employee.last_name.ilike(pattern))
        )

    total = query.count()
    employees = query.offset(skip).limit(limit).all()

    # Batch-load the latest active base salary for all returned employees
    # in a single query to avoid N+1 round trips to Turso.
    _attach_current_base_salary_batch(employees, db)

    return EmployeeListResponse(
        items=employees,
        total=total,
        page=skip // limit,
        page_size=limit,
        total_pages=max(1, (total + limit - 1) // limit) if total > 0 else 1,
    )


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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

    # Validate base salary against UMP
    _validate_ump(db, payload.company_id, payload.entity_id, payload.base_salary)

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
        entity_id=payload.entity_id,
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

    # Store base salary as a history record
    if payload.base_salary is not None:
        _set_base_salary(
            db,
            employee.id,
            payload.base_salary,
            effective_date=payload.base_salary_effective_date or payload.date_joined,
            notes="Gaji pokok awal",
            user_id=current_user.get("user_id"),
        )
        db.commit()
        db.refresh(employee)

    _attach_current_base_salary(employee, db)
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
    _attach_current_base_salary(employee, db)
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
    current_user: dict = Depends(get_current_user),
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

    salary_changed = "base_salary" in update_data
    salary_effective_date = update_data.get("base_salary_effective_date")

    for field, value in update_data.items():
        model_field = field_mapping.get(field, field)
        # Do not overwrite direct employee.base_salary; it is maintained via history
        if model_field == "base_salary":
            continue
        setattr(employee, model_field, value)

    # Validate and store new base salary via history
    if salary_changed:
        new_salary = update_data["base_salary"]
        _validate_ump(db, employee.company_id, employee.entity_id, new_salary)
        if new_salary is not None:
            _set_base_salary(
                db,
                employee.id,
                new_salary,
                effective_date=salary_effective_date or date.today(),
                notes="Perubahan gaji pokok",
                user_id=current_user.get("user_id"),
            )

    # Pull current base salary from history for UMP validation when salary didn't change
    if not salary_changed:
        current_record = _get_latest_base_salary(db, employee.id)
        employee.base_salary = current_record.base_salary if current_record else None

    # Validate base salary against UMP after applying updates
    _validate_ump(db, employee.company_id, employee.entity_id, employee.base_salary)

    # Recompute full_name if name fields changed
    if "first_name" in update_data or "last_name" in update_data:
        first = employee.first_name
        last = employee.last_name
        employee.full_name = f"{first} {last}" if last else first

    db.commit()
    db.refresh(employee)
    _attach_current_base_salary(employee, db)
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


# ─── Employee Salary History & Audit Trail ───────────────────────────────────


@router.get(
    "/{employee_id}/salary-history",
    response_model=List[EmployeeSalaryHistoryResponse],
    summary="List employee base salary history with audit trail",
)
def list_employee_salary_history(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """List all base salary history records for an employee, including audit info."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Employee {employee_id} not found"},
        )

    history = (
        db.query(EmployeeSalaryHistory)
        .filter(EmployeeSalaryHistory.employee_id == employee_id)
        .order_by(EmployeeSalaryHistory.effective_date.desc())
        .all()
    )

    return [
        {
            **record.__dict__,
            "created_by_name": record.creator.full_name if record.creator else None,
            "updated_by_name": record.updater.full_name if record.updater else None,
        }
        for record in history
    ]


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
