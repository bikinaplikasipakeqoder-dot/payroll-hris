"""
Bulk Employee Seeder — generates 200 realistic Indonesian employees with
attendance, overtime, and kasbon data for testing purposes.

Usage:
    python -m app.seed.bulk_seeder
"""

import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from faker import Faker
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models.employee import Employee, Department, Position, EmploymentStatus
from app.models.salary import Grade, GradeSalaryMatrix
from app.models.attendance import AttendanceRecord, OvertimeRecord
from app.models.kasbon import KasbonRequest, KasbonInstallment
from app.models.auth import User


# ---------------------------------------------------------------------------
# Reference data definitions
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    ("PROD", "Production"),
    ("HR", "Human Resources"),
    ("FIN", "Finance"),
    ("IT", "Information Technology"),
    ("SALES", "Sales & Marketing"),
]

POSITIONS = [
    ("STAFF", "Staff"),
    ("SR_STAFF", "Senior Staff"),
    ("SPV", "Supervisor"),
    ("MGR", "Manager"),
    ("DIR", "Director"),
]

GRADES = [
    ("1A", "Grade 1A", Decimal("4000000"), Decimal("5500000")),
    ("1B", "Grade 1B", Decimal("5500000"), Decimal("7000000")),
    ("2A", "Grade 2A", Decimal("7000000"), Decimal("9000000")),
    ("2B", "Grade 2B", Decimal("9000000"), Decimal("11000000")),
    ("3A", "Grade 3A", Decimal("11000000"), Decimal("14000000")),
    ("3B", "Grade 3B", Decimal("14000000"), Decimal("17000000")),
    ("4A", "Grade 4A", Decimal("17000000"), Decimal("21000000")),
    ("4B", "Grade 4B", Decimal("21000000"), Decimal("26000000")),
    ("5A", "Grade 5A", Decimal("26000000"), Decimal("32000000")),
    ("5C", "Grade 5C", Decimal("32000000"), Decimal("45000000")),
]

PTKP_WEIGHTS = {
    "TK/0": 30, "K/0": 20, "TK/1": 15, "K/1": 15,
    "TK/2": 10, "K/2": 5, "K/3": 5,
}

# Approximate Indonesian demographics
RELIGIONS = [
    ("Islam", 870),
    ("Protestan", 70),
    ("Katolik", 30),
    ("Hindu", 20),
    ("Buddha", 10),
]

BANKS = [("BCA", 40), ("Mandiri", 35), ("BNI", 25)]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _ensure_admin_user(db: Session) -> int:
    """Ensure an admin user exists for FK references (approved_by)."""
    user = db.query(User).filter_by(id=1).first()
    if not user:
        user = db.query(User).first()
    if not user:
        user = User(
            username="admin",
            email="admin@company.com",
            password_hash="seeded_placeholder",
            full_name="System Admin",
            is_active=True,
            company_id=1,
        )
        db.add(user)
        db.flush()
        print("[SEED] Created admin user for FK references.")
    return user.id


def _get_or_create_departments(db: Session, company_id: int) -> list[int]:
    """Create departments if they don't exist, return list of IDs."""
    department_ids = []
    for code, name in DEPARTMENTS:
        dept = db.query(Department).filter_by(company_id=company_id, code=code).first()
        if not dept:
            dept = Department(company_id=company_id, code=code, name=name, is_active=True)
            db.add(dept)
            db.flush()
        department_ids.append(dept.id)
    return department_ids


def _get_or_create_positions(db: Session, company_id: int) -> list[int]:
    """Create positions if they don't exist, return list of IDs."""
    position_ids = []
    for code, name in POSITIONS:
        pos = db.query(Position).filter_by(company_id=company_id, code=code).first()
        if not pos:
            pos = Position(company_id=company_id, code=code, name=name, is_active=True)
            db.add(pos)
            db.flush()
        position_ids.append(pos.id)
    return position_ids


def _get_or_create_employment_status(db: Session, company_id: int) -> int:
    """Create 'Karyawan Tetap' status if not exists, return ID."""
    status = db.query(EmploymentStatus).filter_by(
        company_id=company_id, code="TETAP"
    ).first()
    if not status:
        status = EmploymentStatus(
            company_id=company_id,
            code="TETAP",
            name="Karyawan Tetap",
            is_permanent=True,
            is_active=True,
        )
        db.add(status)
        db.flush()
    return status.id


def _get_or_create_grades(db: Session, company_id: int) -> list[Grade]:
    """Create grades + salary matrix if not exist, return Grade objects."""
    grade_objects = []
    for code, name, sal_min, sal_max in GRADES:
        grade = db.query(Grade).filter_by(company_id=company_id, grade_code=code).first()
        if not grade:
            grade = Grade(
                company_id=company_id,
                grade_code=code,
                grade_name=name,
                is_active=True,
            )
            db.add(grade)
            db.flush()
            # Create salary matrix for this grade
            matrix = GradeSalaryMatrix(
                grade_id=grade.id,
                basic_salary_min=sal_min,
                basic_salary_max=sal_max,
                effective_date=date(2024, 1, 1),
                is_active=True,
            )
            db.add(matrix)
            db.flush()
        grade_objects.append(grade)
    return grade_objects


def _random_salary_in_range(sal_min: Decimal, sal_max: Decimal) -> Decimal:
    """Generate a random salary between min and max, rounded to thousands."""
    range_float = float(sal_max - sal_min)
    random_amount = sal_min + Decimal(str(random.uniform(0, range_float)))
    # Round to nearest 100,000
    return (random_amount / Decimal("100000")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    ) * Decimal("100000")


# ---------------------------------------------------------------------------
# Main seeder function
# ---------------------------------------------------------------------------

def seed_bulk_employees(db: Session, company_id: int = 1, count: int = 200):
    """
    Seed bulk employee data with attendance, overtime, and kasbon records.

    Idempotent: skips if employees already meet the target count.
    """
    # --- Idempotency check ---
    existing = db.query(Employee).filter(Employee.company_id == company_id).count()
    if existing >= count:
        print(f"[SKIP] Already have {existing} employees for company {company_id}.")
        return

    # --- Step 1: Create reference data ---
    print("[SEED] Setting up reference data...")
    admin_user_id = _ensure_admin_user(db)
    department_ids = _get_or_create_departments(db, company_id)
    position_ids = _get_or_create_positions(db, company_id)
    status_id = _get_or_create_employment_status(db, company_id)
    grade_objects = _get_or_create_grades(db, company_id)
    db.flush()
    print("[SEED] Reference data ready.")

    # Build grade lookup: grade object -> (min, max)
    grade_salary_map = {}
    for code, name, sal_min, sal_max in GRADES:
        for g in grade_objects:
            if g.grade_code == code:
                grade_salary_map[g.id] = (sal_min, sal_max)
                break

    # --- Step 2: Generate employees ---
    fake = Faker("id_ID")
    Faker.seed(42)
    random.seed(42)

    ptkp_keys = list(PTKP_WEIGHTS.keys())
    ptkp_wts = list(PTKP_WEIGHTS.values())
    religion_names = [r[0] for r in RELIGIONS]
    religion_weights = [r[1] for r in RELIGIONS]
    bank_names = [b[0] for b in BANKS]
    bank_weights = [b[1] for b in BANKS]

    created_employees: list[Employee] = []
    batch: list[Employee] = []

    for i in range(1, count + 1):
        emp_code = f"EMP{i:04d}"
        # Skip if already exists
        if db.query(Employee).filter_by(employee_code=emp_code).first():
            continue

        first_name = fake.first_name()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        gender = random.choice(["M", "F"])
        dob = fake.date_of_birth(minimum_age=22, maximum_age=55)
        personal_id = fake.numerify("################")  # 16 digits
        npwp = fake.numerify("###############") if random.random() < 0.8 else None
        ptkp_status = random.choices(ptkp_keys, weights=ptkp_wts)[0]
        religion = random.choices(religion_names, weights=religion_weights)[0]
        phone = fake.phone_number()
        email = f"{first_name.lower()}.{last_name.lower()}{i}@company.com"

        grade = random.choice(grade_objects)
        sal_min, sal_max = grade_salary_map[grade.id]
        base_salary = _random_salary_in_range(sal_min, sal_max)

        date_joined = fake.date_between(start_date=date(2018, 1, 1), end_date=date(2024, 12, 31))
        bank_name = random.choices(bank_names, weights=bank_weights)[0]

        # Try province first, fallback to state
        try:
            province = fake.province()
        except AttributeError:
            province = fake.state()

        emp = Employee(
            company_id=company_id,
            employee_code=emp_code,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            gender=gender,
            date_of_birth=dob,
            personal_id_number=personal_id,
            npwp=npwp,
            ptkp_status=ptkp_status,
            religion=religion,
            phone=phone,
            email=email,
            department_id=random.choice(department_ids),
            position_id=random.choice(position_ids),
            grade_id=grade.id,
            employment_status_id=status_id,
            base_salary=base_salary,
            date_joined=date_joined,
            bank_name=bank_name,
            bank_account_number=fake.numerify("##########"),
            bank_account_holder_name=full_name,
            bpjs_kesehatan_number=fake.numerify("0000#########"),
            bpjs_ketenagakerjaan_number=fake.numerify("0000#########"),
            address_street=fake.street_address(),
            address_city=fake.city(),
            address_province=province,
            address_postal_code=fake.postcode(),
            is_active=True,
        )
        batch.append(emp)
        created_employees.append(emp)

        if len(batch) >= 50:
            db.add_all(batch)
            db.flush()
            print(f"[SEED] Created employees {i - len(batch) + 1}-{i}/{count}")
            batch = []

    # Flush remaining batch
    if batch:
        db.add_all(batch)
        db.flush()
        print(f"[SEED] Created employees {count - len(batch) + 1}-{count}/{count}")

    print(f"[SEED] Total new employees created: {len(created_employees)}")

    if not created_employees:
        print("[SEED] No new employees to generate data for.")
        return

    # Get all employee IDs for data generation
    employee_ids = [e.id for e in created_employees]

    # --- Step 3: Generate 1-month attendance (June 2026) ---
    _generate_attendance(db, created_employees, employee_ids)

    # --- Step 4: Generate overtime for ~10% of employees ---
    _generate_overtime(db, created_employees, admin_user_id)

    # --- Step 5: Generate kasbon for ~10% of employees ---
    _generate_kasbon(db, created_employees, admin_user_id)


def _generate_attendance(db: Session, employees: list[Employee], employee_ids: list[int]):
    """Generate June 2026 attendance records for all employees."""
    # Calculate working days in June 2026 (Mon-Fri)
    june_working_days = []
    d = date(2026, 6, 1)
    while d.month == 6:
        if d.weekday() < 5:  # Mon-Fri
            june_working_days.append(d)
        d += timedelta(days=1)

    # Check existing attendance to avoid duplicates
    existing_attendance = set(
        (r.employee_id, r.attendance_date)
        for r in db.query(
            AttendanceRecord.employee_id, AttendanceRecord.attendance_date
        ).filter(AttendanceRecord.employee_id.in_(employee_ids)).all()
    )

    statuses = ["PRESENT", "ABSENT", "SICK", "LEAVE"]
    status_weights = [85, 7, 4, 4]

    records = []
    total_created = 0

    for emp in employees:
        for work_date in june_working_days:
            if (emp.id, work_date) in existing_attendance:
                continue

            status = random.choices(statuses, weights=status_weights)[0]

            if status == "PRESENT":
                hours_worked = round(random.uniform(7.5, 9.0), 2)
                is_late = random.random() < 0.10
                late_minutes = random.randint(5, 45) if is_late else 0

                if is_late:
                    check_in_hour = 8
                    check_in_min = 30 + random.randint(0, 15)
                    if check_in_min >= 60:
                        check_in_hour = 9
                        check_in_min -= 60
                else:
                    check_in_hour = 8
                    check_in_min = random.randint(0, 29)

                check_in_time = f"{check_in_hour:02d}:{check_in_min:02d}:00"

                # Compute checkout from check_in + hours_worked
                total_minutes = int(hours_worked * 60)
                out_hour = check_in_hour + (check_in_min + total_minutes) // 60
                out_min = (check_in_min + total_minutes) % 60
                check_out_time = f"{out_hour:02d}:{out_min:02d}:00"

                record = AttendanceRecord(
                    employee_id=emp.id,
                    attendance_date=work_date,
                    status="PRESENT",
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,
                    is_late=is_late,
                    late_minutes=late_minutes,
                    hours_worked=Decimal(str(hours_worked)),
                )
            else:
                record = AttendanceRecord(
                    employee_id=emp.id,
                    attendance_date=work_date,
                    status=status,
                    check_in_time=None,
                    check_out_time=None,
                    is_late=False,
                    late_minutes=0,
                    hours_worked=Decimal("0"),
                )

            records.append(record)
            total_created += 1

            # Batch flush every 500 records
            if len(records) >= 500:
                db.add_all(records)
                db.flush()
                records = []

    # Flush remaining
    if records:
        db.add_all(records)
        db.flush()

    print(f"[SEED] Generated attendance for {len(employees)} employees ({total_created} records)")


def _generate_overtime(db: Session, employees: list[Employee], admin_user_id: int):
    """Generate overtime records for 10% of employees."""
    # Calculate june working days and weekends
    june_working_days = []
    june_weekends = []
    d = date(2026, 6, 1)
    while d.month == 6:
        if d.weekday() < 5:
            june_working_days.append(d)
        else:
            june_weekends.append(d)
        d += timedelta(days=1)

    selected = random.sample(employees, min(20, len(employees)))
    total_records = 0

    for emp in selected:
        num_entries = random.randint(2, 4)
        for _ in range(num_entries):
            ot_type = random.choices(
                ["WEEKDAY", "WEEKEND", "HOLIDAY"], weights=[60, 30, 10]
            )[0]

            if ot_type == "WEEKEND" and june_weekends:
                ot_date = random.choice(june_weekends)
            else:
                ot_date = random.choice(june_working_days)

            hours = Decimal(str(round(random.uniform(1.0, 4.0), 1)))

            if ot_type == "WEEKDAY":
                multiplier = Decimal("1.5")
            elif ot_type == "WEEKEND":
                multiplier = Decimal("2.0")
            else:
                multiplier = Decimal("3.0")

            approval_status = random.choices(
                ["APPROVED", "PENDING"], weights=[80, 20]
            )[0]

            approved_by = admin_user_id if approval_status == "APPROVED" else None

            record = OvertimeRecord(
                employee_id=emp.id,
                overtime_date=ot_date,
                overtime_type=ot_type,
                hours=hours,
                multiplier=multiplier,
                approval_status=approval_status,
                approved_by=approved_by,
            )
            db.add(record)
            total_records += 1

    db.flush()
    print(f"[SEED] Generated overtime records for {len(selected)} employees ({total_records} records)")


def _generate_kasbon(db: Session, employees: list[Employee], admin_user_id: int):
    """Generate kasbon (loan) records for 10% of employees."""
    selected = random.sample(employees, min(20, len(employees)))
    total_requests = 0

    for idx, emp in enumerate(selected, start=1):
        principal_amount = Decimal(str(random.randint(2000000, 5000000)))
        number_of_installments = random.randint(3, 6)
        monthly_installment = (principal_amount / number_of_installments).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )

        kasbon_number = f"KSB-2026-{emp.id:05d}"

        # Check if this kasbon already exists
        existing = db.query(KasbonRequest).filter_by(kasbon_number=kasbon_number).first()
        if existing:
            continue

        kasbon = KasbonRequest(
            employee_id=emp.id,
            kasbon_number=kasbon_number,
            principal_amount=principal_amount,
            purpose="Personal needs",
            request_date=date(2026, 5, 15),
            approval_date=date(2026, 5, 18),
            disbursement_date=date(2026, 5, 20),
            number_of_installments=number_of_installments,
            installment_amount=monthly_installment,
            status="DISBURSED",
            approved_by=admin_user_id,
        )
        db.add(kasbon)
        db.flush()

        # Create installment records
        for inst_num in range(1, number_of_installments + 1):
            # Due on 25th of each month starting June 2026
            due_month = 6 + (inst_num - 1)
            due_year = 2026
            if due_month > 12:
                due_year += (due_month - 1) // 12
                due_month = ((due_month - 1) % 12) + 1

            installment = KasbonInstallment(
                kasbon_request_id=kasbon.id,
                installment_number=inst_num,
                amount=monthly_installment,
                due_date=date(due_year, due_month, 25),
                is_paid=(inst_num == 1),  # First installment already paid
                paid_date=date(2026, 6, 25) if inst_num == 1 else None,
            )
            db.add(installment)

        total_requests += 1

    db.flush()
    print(f"[SEED] Generated kasbon loans for {total_requests} employees")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        # Ensure base seed data exists first
        from app.seed.seed_data import seed_all
        seed_all(db)

        # Now seed bulk employees
        seed_bulk_employees(db, company_id=1, count=200)
        db.commit()
        print("\n\u2705 Bulk seeding complete!")
    except Exception as e:
        db.rollback()
        print(f"\n\u274c Seeding failed: {e}")
        raise
    finally:
        db.close()
