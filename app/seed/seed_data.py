"""
Seed script for Indonesian Payroll & HRIS system.

Seeds the database with Indonesian payroll compliance defaults including:
- System roles and permissions
- PTKP values (2024 regulation)
- Tax brackets Pasal 17 (UU HPP)
- BPJS settings
- Overtime settings
- Languages
- Leave types
- Tax settings
- Default company
"""

from datetime import date
from decimal import Decimal

from app.database import SessionLocal
from app.models import (
    Company, Role, Permission, RolePermission,
    PtkpValue, TaxBracketPasal17, BpjsSetting,
    OvertimeSetting, Language, LeaveType, TaxSetting,
    Entity, UmpSetting, RuleCategory, RuleVariable,
)


def seed_all(db_session):
    """Seed all default data. Idempotent — checks before inserting."""

    # 1. Default Company
    _seed_company(db_session)

    # 2. Roles
    _seed_roles(db_session)

    # 3. Permissions
    _seed_permissions(db_session)

    # 4. Role-Permission mappings
    _seed_role_permissions(db_session)

    # 5. PTKP Values
    _seed_ptkp_values(db_session)

    # 6. Tax Brackets Pasal 17
    _seed_tax_brackets(db_session)

    # 7. BPJS Settings
    _seed_bpjs_settings(db_session)

    # 8. Overtime Settings
    _seed_overtime_settings(db_session)

    # 9. Languages
    _seed_languages(db_session)

    # 10. Leave Types
    _seed_leave_types(db_session)

    # 11. Tax Settings
    _seed_tax_settings(db_session)

    # 12. Default Entity / Branch
    _seed_default_entity(db_session)

    # 13. Default UMP Settings
    _seed_ump_settings(db_session)

    # 14. Rules Engine defaults
    _seed_rule_categories(db_session)
    _seed_rule_variables(db_session)

    print("[SEED] All seed data completed successfully.")


def _seed_company(db_session):
    """Seed default company."""
    existing = db_session.query(Company).filter_by(name="My Company").first()
    if existing:
        print("[SEED] Company already exists, skipping.")
        return

    company = Company(
        name="My Company",
        work_week_days=5,
        payroll_method="GROSS",
        default_language="id",
        is_active=True,
    )
    db_session.add(company)
    db_session.commit()
    print("[SEED] Default company created (id=1).")


def _seed_roles(db_session):
    """Seed 6 system roles."""
    role_names = [
        ("Administrator", "Full system access"),
        ("Payroll Master", "Payroll processing and tax management"),
        ("Operator", "Employee and operational data management"),
        ("Reporting", "Read-only access with reporting capabilities"),
        ("Payment", "Payment approval and disbursement"),
        ("Employee", "Self-service employee access"),
    ]

    existing_count = db_session.query(Role).filter(
        Role.name.in_([r[0] for r in role_names])
    ).count()

    if existing_count >= len(role_names):
        print("[SEED] Roles already exist, skipping.")
        return

    for name, description in role_names:
        exists = db_session.query(Role).filter_by(name=name).first()
        if not exists:
            db_session.add(Role(name=name, description=description, is_system=True))

    db_session.commit()
    print(f"[SEED] Roles seeded ({len(role_names)} roles).")


def _seed_permissions(db_session):
    """Seed permissions for key resource-action combinations."""
    resources = [
        "EMPLOYEE", "PAYROLL", "ATTENDANCE", "LEAVE",
        "KASBON", "BONUS", "TAX", "BPJS", "COMPANY", "REPORT", "AI",
    ]
    actions = ["READ", "CREATE", "UPDATE", "DELETE", "APPROVE"]

    existing_count = db_session.query(Permission).count()
    if existing_count > 0:
        print("[SEED] Permissions already exist, skipping.")
        return

    permissions = []
    for resource in resources:
        for action in actions:
            perm_name = f"{resource}.{action}"
            permissions.append(Permission(
                name=perm_name,
                description=f"{action} access to {resource}",
                resource=resource,
                action=action,
            ))

    db_session.add_all(permissions)
    db_session.commit()
    print(f"[SEED] Permissions seeded ({len(permissions)} permissions).")


def _seed_role_permissions(db_session):
    """Seed role-permission mappings."""
    existing_count = db_session.query(RolePermission).count()
    if existing_count > 0:
        print("[SEED] Role-Permission mappings already exist, skipping.")
        return

    # Get roles
    roles = {r.name: r.id for r in db_session.query(Role).all()}
    # Get permissions
    perms = {p.name: p.id for p in db_session.query(Permission).all()}

    if not roles or not perms:
        print("[SEED] Roles or permissions not found, skipping role-permission mapping.")
        return

    mappings = []

    # Administrator: all permissions
    admin_id = roles.get("Administrator")
    if admin_id:
        for perm_id in perms.values():
            mappings.append(RolePermission(role_id=admin_id, permission_id=perm_id))

    # Payroll Master: PAYROLL.*, TAX.*, BPJS.*, EMPLOYEE.READ, ATTENDANCE.READ,
    #                 LEAVE.READ, KASBON.READ, BONUS.READ, REPORT.*
    payroll_master_id = roles.get("Payroll Master")
    if payroll_master_id:
        pm_perms = [p for p in perms if (
            p.startswith("PAYROLL.") or
            p.startswith("TAX.") or
            p.startswith("BPJS.") or
            p.startswith("REPORT.") or
            p in ("EMPLOYEE.READ", "ATTENDANCE.READ", "LEAVE.READ", "KASBON.READ", "BONUS.READ")
        )]
        for perm_name in pm_perms:
            mappings.append(RolePermission(role_id=payroll_master_id, permission_id=perms[perm_name]))

    # Operator: EMPLOYEE.*, ATTENDANCE.*, LEAVE.*, KASBON.*, BONUS.*
    operator_id = roles.get("Operator")
    if operator_id:
        op_perms = [p for p in perms if (
            p.startswith("EMPLOYEE.") or
            p.startswith("ATTENDANCE.") or
            p.startswith("LEAVE.") or
            p.startswith("KASBON.") or
            p.startswith("BONUS.")
        )]
        for perm_name in op_perms:
            mappings.append(RolePermission(role_id=operator_id, permission_id=perms[perm_name]))

    # Reporting: *.READ, REPORT.*
    reporting_id = roles.get("Reporting")
    if reporting_id:
        rp_perms = [p for p in perms if (
            p.endswith(".READ") or
            p.startswith("REPORT.")
        )]
        for perm_name in rp_perms:
            mappings.append(RolePermission(role_id=reporting_id, permission_id=perms[perm_name]))

    # Payment: PAYROLL.READ, PAYROLL.APPROVE, REPORT.READ
    payment_id = roles.get("Payment")
    if payment_id:
        pay_perms = ["PAYROLL.READ", "PAYROLL.APPROVE", "REPORT.READ"]
        for perm_name in pay_perms:
            if perm_name in perms:
                mappings.append(RolePermission(role_id=payment_id, permission_id=perms[perm_name]))

    # Employee: EMPLOYEE.READ, ATTENDANCE.READ, LEAVE.READ, LEAVE.CREATE
    employee_id = roles.get("Employee")
    if employee_id:
        emp_perms = ["EMPLOYEE.READ", "ATTENDANCE.READ", "LEAVE.READ", "LEAVE.CREATE"]
        for perm_name in emp_perms:
            if perm_name in perms:
                mappings.append(RolePermission(role_id=employee_id, permission_id=perms[perm_name]))

    db_session.add_all(mappings)
    db_session.commit()
    print(f"[SEED] Role-Permission mappings seeded ({len(mappings)} mappings).")


def _seed_ptkp_values(db_session):
    """Seed PTKP values for 2024 regulation."""
    existing = db_session.query(PtkpValue).filter_by(regulation_year=2024).count()
    if existing > 0:
        print("[SEED] PTKP values already exist, skipping.")
        return

    company = db_session.query(Company).first()
    company_id = company.id if company else 1

    ptkp_data = [
        ("TK/0", "Tidak Kawin tanpa tanggungan", 54000000, 4500000),
        ("TK/1", "Tidak Kawin dengan 1 tanggungan", 58500000, 4875000),
        ("TK/2", "Tidak Kawin dengan 2 tanggungan", 63000000, 5250000),
        ("TK/3", "Tidak Kawin dengan 3 tanggungan", 67500000, 5625000),
        ("K/0", "Kawin tanpa tanggungan", 58500000, 4875000),
        ("K/1", "Kawin dengan 1 tanggungan", 63000000, 5250000),
        ("K/2", "Kawin dengan 2 tanggungan", 67500000, 5625000),
        ("K/3", "Kawin dengan 3 tanggungan", 72000000, 6000000),
    ]

    records = []
    for code, desc, annual, monthly in ptkp_data:
        records.append(PtkpValue(
            company_id=company_id,
            ptkp_code=code,
            description=desc,
            annual_amount=Decimal(str(annual)),
            monthly_amount=Decimal(str(monthly)),
            regulation_year=2024,
            effective_date=date(2024, 1, 1),
            is_active=True,
        ))

    db_session.add_all(records)
    db_session.commit()
    print(f"[SEED] PTKP values seeded ({len(records)} records).")


def _seed_tax_brackets(db_session):
    """Seed tax brackets Pasal 17 (UU HPP 2024)."""
    existing = db_session.query(TaxBracketPasal17).filter_by(regulation_year=2024).count()
    if existing > 0:
        print("[SEED] Tax brackets already exist, skipping.")
        return

    company = db_session.query(Company).first()
    company_id = company.id if company else 1

    brackets = [
        (1, 0, 60000000, Decimal("0.05")),
        (2, 60000000, 250000000, Decimal("0.15")),
        (3, 250000000, 500000000, Decimal("0.25")),
        (4, 500000000, 5000000000, Decimal("0.30")),
        (5, 5000000000, None, Decimal("0.35")),
    ]

    records = []
    for order, range_min, range_max, rate in brackets:
        records.append(TaxBracketPasal17(
            company_id=company_id,
            bracket_order=order,
            income_range_min=Decimal(str(range_min)),
            income_range_max=Decimal(str(range_max)) if range_max is not None else None,
            tax_rate=rate,
            regulation_year=2024,
            effective_date=date(2024, 1, 1),
            is_active=True,
        ))

    db_session.add_all(records)
    db_session.commit()
    print(f"[SEED] Tax brackets Pasal 17 seeded ({len(records)} brackets).")


def _seed_bpjs_settings(db_session):
    """Seed BPJS settings effective 2024-01-01."""
    existing = db_session.query(BpjsSetting).count()
    if existing > 0:
        print("[SEED] BPJS settings already exist, skipping.")
        return

    company = db_session.query(Company).first()
    company_id = company.id if company else 1

    bpjs_data = [
        ("KESEHATAN", Decimal("0.01"), Decimal("0.04"), Decimal("12000000")),
        ("JHT", Decimal("0.02"), Decimal("0.037"), None),
        ("JP", Decimal("0.01"), Decimal("0.02"), Decimal("9559600")),
        ("JKK", Decimal("0"), Decimal("0.0024"), None),
        ("JKM", Decimal("0"), Decimal("0.003"), None),
    ]

    records = []
    for bpjs_type, emp_rate, empr_rate, max_salary in bpjs_data:
        records.append(BpjsSetting(
            company_id=company_id,
            bpjs_type=bpjs_type,
            employee_rate=emp_rate,
            employer_rate=empr_rate,
            max_salary_base=max_salary,
            regulation_year=2024,
            effective_date=date(2024, 1, 1),
            is_active=True,
        ))

    db_session.add_all(records)
    db_session.commit()
    print(f"[SEED] BPJS settings seeded ({len(records)} records).")


def _seed_overtime_settings(db_session):
    """Seed default overtime settings."""
    existing = db_session.query(OvertimeSetting).count()
    if existing > 0:
        print("[SEED] Overtime settings already exist, skipping.")
        return

    company = db_session.query(Company).first()
    company_id = company.id if company else 1

    setting = OvertimeSetting(
        company_id=company_id,
        work_week_type="5_DAY",
        weekday_first_hour_multiplier=Decimal("1.5"),
        weekday_subsequent_multiplier=Decimal("2.0"),
        weekend_first_hour_multiplier=Decimal("2.0"),
        weekend_subsequent_multiplier=Decimal("3.0"),
        late_penalty_per_minute=Decimal("0"),
        is_active=True,
    )
    db_session.add(setting)
    db_session.commit()
    print("[SEED] Overtime settings seeded.")


def _seed_languages(db_session):
    """Seed supported languages."""
    existing = db_session.query(Language).count()
    if existing > 0:
        print("[SEED] Languages already exist, skipping.")
        return

    languages = [
        Language(language_code="id", language_name="Indonesian", is_default=True, is_active=True),
        Language(language_code="en", language_name="English", is_default=False, is_active=True),
    ]
    db_session.add_all(languages)
    db_session.commit()
    print("[SEED] Languages seeded (id, en).")


def _seed_leave_types(db_session):
    """Seed default leave types."""
    existing = db_session.query(LeaveType).count()
    if existing > 0:
        print("[SEED] Leave types already exist, skipping.")
        return

    company = db_session.query(Company).first()
    company_id = company.id if company else 1

    leave_types = [
        ("ANNUAL", "Annual Leave", 12, True),
        ("SICK", "Sick Leave", 14, True),
        ("MATERNITY", "Maternity Leave", 90, True),
        ("PATERNITY", "Paternity Leave", 2, True),
        ("PERSONAL", "Personal Leave", 3, True),
        ("UNPAID", "Unpaid Leave", 0, False),
    ]

    records = []
    for code, name, entitlement, is_paid in leave_types:
        records.append(LeaveType(
            company_id=company_id,
            name=name,
            code=code,
            default_annual_entitlement=entitlement,
            is_paid=is_paid,
            requires_approval=True,
            is_active=True,
        ))

    db_session.add_all(records)
    db_session.commit()
    print(f"[SEED] Leave types seeded ({len(records)} types).")


def _seed_tax_settings(db_session):
    """Seed default tax settings."""
    existing = db_session.query(TaxSetting).count()
    if existing > 0:
        print("[SEED] Tax settings already exist, skipping.")
        return

    company = db_session.query(Company).first()
    company_id = company.id if company else 1

    setting = TaxSetting(
        company_id=company_id,
        tax_calculation_method="PASAL_17",
        is_active=True,
    )
    db_session.add(setting)
    db_session.commit()
    print("[SEED] Tax settings seeded (PASAL_17).")


def _seed_default_entity(db_session):
    """Seed a default entity/branch for the company."""
    existing = db_session.query(Entity).count()
    if existing > 0:
        print("[SEED] Entities already exist, skipping.")
        return

    company = db_session.query(Company).first()
    company_id = company.id if company else 1

    entity = Entity(
        company_id=company_id,
        code="HQ",
        name="Kantor Pusat",
        city="Jakarta Selatan",
        province="DKI Jakarta",
        is_active=True,
    )
    db_session.add(entity)
    db_session.commit()
    print("[SEED] Default entity seeded (HQ).")


def _seed_rule_categories(db_session):
    """Seed default rule categories."""
    categories = [
        ("BPJS", "BPJS Configuration", "Rates and ceilings for BPJS Kesehatan, JHT, JP, JKK, JKM"),
        ("PPH21", "PPh 21 Configuration", "Tax brackets, TER brackets, and PTKP values"),
        ("OVERTIME", "Overtime Configuration", "Overtime multipliers and hourly divisor"),
        ("ALLOWANCE", "Allowance Configuration", "Formula-based allowance calculation rules"),
    ]
    existing = db_session.query(RuleCategory).filter(
        RuleCategory.category_code.in_([c[0] for c in categories])
    ).count()
    if existing >= len(categories):
        print("[SEED] Rule categories already exist, skipping.")
        return

    for code, name, description in categories:
        if not db_session.query(RuleCategory).filter_by(category_code=code).first():
            db_session.add(RuleCategory(
                category_code=code,
                category_name=name,
                description=description,
                is_active=True,
            ))
    db_session.commit()
    print(f"[SEED] Rule categories seeded ({len(categories)} categories).")


def _seed_rule_variables(db_session):
    """Seed default rule variables."""
    variables = [
        ("basic_salary", "Basic Salary", "EMPLOYEE_FIELD", "employees", "base_salary", "Employee base salary"),
        ("ptkp_status", "PTKP Status", "EMPLOYEE_FIELD", "employees", "ptkp_status", "Employee PTKP status"),
        ("ptkp_value", "PTKP Value", "CALCULATED", None, None, "Annual PTKP threshold based on ptkp_status"),
        ("bpjs_base", "BPJS Base", "CALCULATED", None, None, "BPJS calculation base (salary + eligible allowances)"),
        ("monthly_gross", "Monthly Gross Income", "CALCULATED", None, None, "Total monthly gross income"),
    ]
    existing = db_session.query(RuleVariable).filter(
        RuleVariable.variable_code.in_([v[0] for v in variables])
    ).count()
    if existing >= len(variables):
        print("[SEED] Rule variables already exist, skipping.")
        return

    for code, name, vtype, table, field, description in variables:
        if not db_session.query(RuleVariable).filter_by(variable_code=code).first():
            db_session.add(RuleVariable(
                variable_code=code,
                variable_name=name,
                variable_type=vtype,
                source_table=table,
                source_field=field,
                description=description,
                is_active=True,
            ))
    db_session.commit()
    print(f"[SEED] Rule variables seeded ({len(variables)} variables).")


def _seed_ump_settings(db_session):
    """Seed default UMP settings for major provinces."""
    existing = db_session.query(UmpSetting).count()
    if existing > 0:
        print("[SEED] UMP settings already exist, skipping.")
        return

    company = db_session.query(Company).first()
    company_id = company.id if company else 1

    ump_data = [
        ("DKI Jakarta", None, 5_067_381),
        ("Jawa Barat", None, 2_057_495),
        ("Jawa Tengah", None, 2_036_947),
        ("Jawa Timur", None, 2_165_244),
        ("Banten", None, 2_902_060),
        ("Yogyakarta", None, 2_125_000),
        ("Bali", None, 2_813_672),
        ("Sumatera Utara", None, 2_809_689),
        ("Sulawesi Selatan", None, 3_200_000),
        ("Kalimantan Timur", None, 3_200_000),
    ]

    records = []
    for province, city, amount in ump_data:
        records.append(UmpSetting(
            company_id=company_id,
            province=province,
            city=city,
            amount=Decimal(str(amount)),
            effective_date=date(2026, 1, 1),
            is_active=True,
        ))

    db_session.add_all(records)
    db_session.commit()
    print(f"[SEED] UMP settings seeded ({len(records)} regions).")


if __name__ == "__main__":
    print("=" * 60)
    print("Indonesian Payroll & HRIS - Database Seeder")
    print("=" * 60)
    db = SessionLocal()
    try:
        seed_all(db)
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seed failed: {e}")
        raise
    finally:
        db.close()
    print("=" * 60)
    print("Seeding complete!")
    print("=" * 60)
