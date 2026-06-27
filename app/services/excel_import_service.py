"""Excel import service for bulk data operations."""

import re
from io import BytesIO
from datetime import date, datetime
from typing import Optional

import pandas as pd
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models.bonus import Bonus, BonusType, Reimbursement, ReimbursementType, THRRecord
from app.models.employee import Department, Employee
from app.models.kasbon import KasbonRequest
from app.models.salary import AllowanceType, EmployeeAllowance, Grade
from app.models.attendance import AttendanceRecord


VALID_PTKP = {"TK/0", "TK/1", "TK/2", "TK/3", "K/0", "K/1", "K/2", "K/3"}
VALID_GENDERS = {"M", "F"}
VALID_ATTENDANCE_STATUSES = {"PRESENT", "ABSENT", "LEAVE", "SICK", "PERMITTED"}
VALID_BONUS_STATUS = {"PENDING", "APPROVED", "REJECTED"}
VALID_REIMBURSEMENT_STATUS = {"PENDING", "APPROVED", "REJECTED"}
VALID_THR_HOLIDAYS = {"IDUL_FITRI", "CHRISTMAS", "NYEPI", "WAISAK"}
VALID_THR_BASIS = {"BASE_SALARY", "PRORATED"}
VALID_KASBON_STATUS = {"PENDING", "APPROVED", "DISBURSED", "COMPLETED", "REJECTED"}


class ExcelImportService:
    """Service for importing data from Excel files."""

    @staticmethod
    def _validate_npwp(value) -> bool:
        """Validate NPWP format (15-16 digits)."""
        if value is None or str(value).strip() == "" or str(value).strip().lower() == "nan":
            return True  # NPWP is optional
        return bool(re.match(r"^\d{15,16}$", str(value).strip()))

    @staticmethod
    def _generate_error_report(errors: list[dict]) -> bytes:
        """Generate an Excel error report from a list of error dicts."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Error Report"
        ws.append(["Row", "Code", "Field", "Error Message"])
        for err in errors:
            ws.append([err.get("row"), err.get("code", ""), err.get("field", ""), err.get("message", "")])
        output = BytesIO()
        wb.save(output)
        return output.getvalue()

    @staticmethod
    def _parse_date(value) -> Optional[date]:
        """Parse a date value from Excel (could be datetime, string, or NaT)."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, (datetime, date)):
            return value if isinstance(value, date) else value.date()
        try:
            return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_str(value) -> Optional[str]:
        """Convert a value to stripped string, returning None for NaN/empty."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        s = str(value).strip()
        return s if s and s.lower() != "nan" else None

    @staticmethod
    def import_employees(file_bytes: bytes, company_id: int, db: Session) -> tuple[dict, Optional[bytes]]:
        """
        Import employees from Excel file.

        Returns (result_dict, error_bytes_or_None).
        """
        df = pd.read_excel(BytesIO(file_bytes))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Pre-load existing employee codes
        existing_codes = set(
            row[0] for row in db.query(Employee.employee_code).all()
        )

        # Pre-load department lookup (company_id, code) -> id
        dept_map = {
            row.code: row.id
            for row in db.query(Department.id, Department.code).filter(
                Department.company_id == company_id
            ).all()
        }

        # Pre-load grade lookup (company_id, grade_code) -> id
        grade_map = {
            row.grade_code: row.id
            for row in db.query(Grade.id, Grade.grade_code).filter(
                Grade.company_id == company_id
            ).all()
        }

        errors = []
        valid_employees = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number (1-indexed header + data)
            row_errors = []

            emp_code = ExcelImportService._safe_str(row.get("employee_code"))
            first_name = ExcelImportService._safe_str(row.get("first_name"))
            date_joined = ExcelImportService._parse_date(row.get("date_joined"))

            # Required field validation
            if not emp_code:
                row_errors.append({"row": row_num, "code": emp_code or "", "field": "employee_code", "message": "employee_code is required"})
            if not first_name:
                row_errors.append({"row": row_num, "code": emp_code or "", "field": "first_name", "message": "first_name is required"})
            if not date_joined:
                row_errors.append({"row": row_num, "code": emp_code or "", "field": "date_joined", "message": "date_joined is required or invalid format (YYYY-MM-DD)"})

            if row_errors:
                errors.extend(row_errors)
                continue

            # Duplicate check
            if emp_code in existing_codes:
                errors.append({"row": row_num, "code": emp_code, "field": "employee_code", "message": f"Duplicate employee_code: {emp_code}"})
                continue

            # NPWP validation
            npwp_val = ExcelImportService._safe_str(row.get("npwp"))
            if npwp_val and not ExcelImportService._validate_npwp(npwp_val):
                errors.append({"row": row_num, "code": emp_code, "field": "npwp", "message": f"Invalid NPWP format (must be 15-16 digits): {npwp_val}"})
                continue

            # PTKP validation
            ptkp = ExcelImportService._safe_str(row.get("ptkp_status"))
            if ptkp and ptkp not in VALID_PTKP:
                errors.append({"row": row_num, "code": emp_code, "field": "ptkp_status", "message": f"Invalid PTKP status: {ptkp}. Must be one of {VALID_PTKP}"})
                continue

            # Gender validation
            gender = ExcelImportService._safe_str(row.get("gender"))
            if gender and gender not in VALID_GENDERS:
                errors.append({"row": row_num, "code": emp_code, "field": "gender", "message": f"Invalid gender: {gender}. Must be M or F"})
                continue

            # FK resolution
            dept_code = ExcelImportService._safe_str(row.get("department_code"))
            dept_id = dept_map.get(dept_code) if dept_code else None
            if dept_code and dept_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "department_code", "message": f"Department not found: {dept_code}"})
                continue

            grade_code = ExcelImportService._safe_str(row.get("grade_code"))
            grade_id = grade_map.get(grade_code) if grade_code else None
            if grade_code and grade_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "grade_code", "message": f"Grade not found: {grade_code}"})
                continue

            last_name = ExcelImportService._safe_str(row.get("last_name")) or ""
            full_name = f"{first_name} {last_name}".strip()

            base_salary_val = row.get("base_salary")
            base_salary = None
            if base_salary_val is not None and not (isinstance(base_salary_val, float) and pd.isna(base_salary_val)):
                try:
                    base_salary = float(base_salary_val)
                except (ValueError, TypeError):
                    pass

            employee = Employee(
                company_id=company_id,
                employee_code=emp_code,
                first_name=first_name,
                last_name=last_name if last_name else None,
                full_name=full_name,
                gender=gender,
                date_of_birth=ExcelImportService._parse_date(row.get("date_of_birth")),
                npwp=npwp_val,
                ptkp_status=ptkp or "TK/0",
                phone=ExcelImportService._safe_str(row.get("phone")),
                email=ExcelImportService._safe_str(row.get("email")),
                department_id=dept_id,
                grade_id=grade_id,
                date_joined=date_joined,
                bank_name=ExcelImportService._safe_str(row.get("bank_name")),
                bank_account_number=ExcelImportService._safe_str(row.get("bank_account_number")),
                bank_account_holder_name=ExcelImportService._safe_str(row.get("bank_account_name")),
                bpjs_kesehatan_number=ExcelImportService._safe_str(row.get("bpjs_kes_number")),
                bpjs_ketenagakerjaan_number=ExcelImportService._safe_str(row.get("bpjs_tk_number")),
                base_salary=base_salary,
                is_active=True,
            )
            valid_employees.append(employee)
            existing_codes.add(emp_code)  # Track for within-file duplicates

        # Batch insert
        if valid_employees:
            for i in range(0, len(valid_employees), 50):
                batch = valid_employees[i:i + 50]
                db.add_all(batch)
                db.flush()
            db.commit()

        result = {
            "total_rows": total_rows,
            "success_count": len(valid_employees),
            "error_count": len(errors),
            "errors": [{"row": e["row"], "field": e.get("field"), "message": e["message"]} for e in errors],
        }

        error_bytes = ExcelImportService._generate_error_report(errors) if errors else None
        return result, error_bytes

    @staticmethod
    def import_attendance(file_bytes: bytes, company_id: int, db: Session) -> tuple[dict, Optional[bytes]]:
        """
        Import attendance records from Excel file.

        Returns (result_dict, error_bytes_or_None).
        """
        df = pd.read_excel(BytesIO(file_bytes))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Pre-load employee code -> id map for this company
        emp_map = {
            row.employee_code: row.id
            for row in db.query(Employee.id, Employee.employee_code).filter(
                Employee.company_id == company_id
            ).all()
        }

        # Pre-load existing attendance (employee_id, date) pairs
        existing_attendance = set(
            (row.employee_id, row.attendance_date)
            for row in db.query(
                AttendanceRecord.employee_id, AttendanceRecord.attendance_date
            ).join(Employee, AttendanceRecord.employee_id == Employee.id).filter(
                Employee.company_id == company_id
            ).all()
        )

        errors = []
        valid_records = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2
            emp_code = ExcelImportService._safe_str(row.get("employee_code"))

            if not emp_code:
                errors.append({"row": row_num, "code": "", "field": "employee_code", "message": "employee_code is required"})
                continue

            emp_id = emp_map.get(emp_code)
            if emp_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "employee_code", "message": f"Employee not found: {emp_code}"})
                continue

            att_date = ExcelImportService._parse_date(row.get("attendance_date"))
            if not att_date:
                errors.append({"row": row_num, "code": emp_code, "field": "attendance_date", "message": "attendance_date is required or invalid format"})
                continue

            status = ExcelImportService._safe_str(row.get("status"))
            if not status or status.upper() not in VALID_ATTENDANCE_STATUSES:
                errors.append({"row": row_num, "code": emp_code, "field": "status", "message": f"Invalid status: {status}. Must be one of {VALID_ATTENDANCE_STATUSES}"})
                continue
            status = status.upper()

            # Unique check
            if (emp_id, att_date) in existing_attendance:
                errors.append({"row": row_num, "code": emp_code, "field": "attendance_date", "message": f"Duplicate attendance record for {emp_code} on {att_date}"})
                continue

            hours_worked = row.get("hours_worked")
            if hours_worked is not None and not (isinstance(hours_worked, float) and pd.isna(hours_worked)):
                try:
                    hours_worked = float(hours_worked)
                except (ValueError, TypeError):
                    hours_worked = None
            else:
                hours_worked = None

            is_late_val = row.get("is_late")
            is_late = False
            if is_late_val is not None and not (isinstance(is_late_val, float) and pd.isna(is_late_val)):
                is_late = str(is_late_val).strip().lower() in ("true", "1", "yes")

            late_mins = row.get("late_minutes")
            if late_mins is not None and not (isinstance(late_mins, float) and pd.isna(late_mins)):
                try:
                    late_mins = int(float(late_mins))
                except (ValueError, TypeError):
                    late_mins = 0
            else:
                late_mins = 0

            record = AttendanceRecord(
                employee_id=emp_id,
                attendance_date=att_date,
                status=status,
                check_in_time=ExcelImportService._safe_str(row.get("check_in_time")),
                check_out_time=ExcelImportService._safe_str(row.get("check_out_time")),
                hours_worked=hours_worked,
                is_late=is_late,
                late_minutes=late_mins,
                notes=ExcelImportService._safe_str(row.get("notes")),
            )
            valid_records.append(record)
            existing_attendance.add((emp_id, att_date))  # Track within-file duplicates

        # Batch insert
        if valid_records:
            for i in range(0, len(valid_records), 50):
                batch = valid_records[i:i + 50]
                db.add_all(batch)
                db.flush()
            db.commit()

        result = {
            "total_rows": total_rows,
            "success_count": len(valid_records),
            "error_count": len(errors),
            "errors": [{"row": e["row"], "field": e.get("field"), "message": e["message"]} for e in errors],
        }

        error_bytes = ExcelImportService._generate_error_report(errors) if errors else None
        return result, error_bytes

    @staticmethod
    def import_allowances(file_bytes: bytes, company_id: int, db: Session) -> tuple[dict, Optional[bytes]]:
        """
        Import employee allowances from Excel file.

        Returns (result_dict, error_bytes_or_None).
        """
        df = pd.read_excel(BytesIO(file_bytes))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Pre-load employee code -> id map
        emp_map = {
            row.employee_code: row.id
            for row in db.query(Employee.id, Employee.employee_code).filter(
                Employee.company_id == company_id
            ).all()
        }

        # Pre-load allowance type code -> id map
        allowance_map = {
            row.code: row.id
            for row in db.query(AllowanceType.id, AllowanceType.code).filter(
                AllowanceType.company_id == company_id
            ).all()
        }

        errors = []
        valid_allowances = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2
            emp_code = ExcelImportService._safe_str(row.get("employee_code"))

            if not emp_code:
                errors.append({"row": row_num, "code": "", "field": "employee_code", "message": "employee_code is required"})
                continue

            emp_id = emp_map.get(emp_code)
            if emp_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "employee_code", "message": f"Employee not found: {emp_code}"})
                continue

            allowance_code = ExcelImportService._safe_str(row.get("allowance_code"))
            if not allowance_code:
                errors.append({"row": row_num, "code": emp_code, "field": "allowance_code", "message": "allowance_code is required"})
                continue

            allowance_type_id = allowance_map.get(allowance_code)
            if allowance_type_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "allowance_code", "message": f"Allowance type not found: {allowance_code}"})
                continue

            # Amount validation
            amount_val = row.get("amount")
            try:
                amount = float(amount_val)
                if amount <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({"row": row_num, "code": emp_code, "field": "amount", "message": "amount must be a positive number"})
                continue

            effective_date = ExcelImportService._parse_date(row.get("effective_date"))
            if not effective_date:
                errors.append({"row": row_num, "code": emp_code, "field": "effective_date", "message": "effective_date is required or invalid format"})
                continue

            end_date = ExcelImportService._parse_date(row.get("end_date"))

            allowance = EmployeeAllowance(
                employee_id=emp_id,
                allowance_type_id=allowance_type_id,
                amount=amount,
                effective_date=effective_date,
                end_date=end_date,
                notes=ExcelImportService._safe_str(row.get("notes")),
                is_active=True,
            )
            valid_allowances.append(allowance)

        # Batch insert
        if valid_allowances:
            for i in range(0, len(valid_allowances), 50):
                batch = valid_allowances[i:i + 50]
                db.add_all(batch)
                db.flush()
            db.commit()

        result = {
            "total_rows": total_rows,
            "success_count": len(valid_allowances),
            "error_count": len(errors),
            "errors": [{"row": e["row"], "field": e.get("field"), "message": e["message"]} for e in errors],
        }

        error_bytes = ExcelImportService._generate_error_report(errors) if errors else None
        return result, error_bytes

    @staticmethod
    def import_bonuses(file_bytes: bytes, company_id: int, db: Session) -> tuple[dict, Optional[bytes]]:
        """Bulk import bonus records from Excel file."""
        df = pd.read_excel(BytesIO(file_bytes))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        emp_map = {
            row.employee_code: row.id
            for row in db.query(Employee.id, Employee.employee_code).filter(
                Employee.company_id == company_id
            ).all()
        }
        type_map = {
            row.code: row.id
            for row in db.query(BonusType.id, BonusType.code).filter(
                BonusType.company_id == company_id
            ).all()
        }

        errors = []
        valid_records = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2
            emp_code = ExcelImportService._safe_str(row.get("employee_code"))
            type_code = ExcelImportService._safe_str(row.get("bonus_type_code"))

            if not emp_code:
                errors.append({"row": row_num, "code": "", "field": "employee_code", "message": "employee_code is required"})
                continue
            emp_id = emp_map.get(emp_code)
            if emp_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "employee_code", "message": f"Employee not found: {emp_code}"})
                continue

            if not type_code:
                errors.append({"row": row_num, "code": emp_code, "field": "bonus_type_code", "message": "bonus_type_code is required"})
                continue
            type_id = type_map.get(type_code)
            if type_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "bonus_type_code", "message": f"Bonus type not found: {type_code}"})
                continue

            try:
                amount = float(row.get("amount"))
                if amount <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({"row": row_num, "code": emp_code, "field": "amount", "message": "amount must be a positive number"})
                continue

            bonus_date = ExcelImportService._parse_date(row.get("bonus_date"))
            if not bonus_date:
                errors.append({"row": row_num, "code": emp_code, "field": "bonus_date", "message": "bonus_date is required or invalid format (YYYY-MM-DD)"})
                continue

            status = ExcelImportService._safe_str(row.get("approval_status")) or "PENDING"
            if status not in VALID_BONUS_STATUS:
                errors.append({"row": row_num, "code": emp_code, "field": "approval_status", "message": f"Invalid status: {status}"})
                continue

            valid_records.append(Bonus(
                employee_id=emp_id,
                bonus_type_id=type_id,
                amount=amount,
                bonus_date=bonus_date,
                description=ExcelImportService._safe_str(row.get("description")),
                approval_status=status,
            ))

        if valid_records:
            for i in range(0, len(valid_records), 50):
                db.add_all(valid_records[i:i + 50])
                db.flush()
            db.commit()

        result = {
            "total_rows": total_rows,
            "success_count": len(valid_records),
            "error_count": len(errors),
            "errors": [{"row": e["row"], "field": e.get("field"), "message": e["message"]} for e in errors],
        }
        error_bytes = ExcelImportService._generate_error_report(errors) if errors else None
        return result, error_bytes

    @staticmethod
    def import_thr(file_bytes: bytes, company_id: int, db: Session) -> tuple[dict, Optional[bytes]]:
        """Bulk import THR records from Excel file."""
        df = pd.read_excel(BytesIO(file_bytes))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        emp_map = {
            row.employee_code: row.id
            for row in db.query(Employee.id, Employee.employee_code).filter(
                Employee.company_id == company_id
            ).all()
        }

        errors = []
        valid_records = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2
            emp_code = ExcelImportService._safe_str(row.get("employee_code"))

            if not emp_code:
                errors.append({"row": row_num, "code": "", "field": "employee_code", "message": "employee_code is required"})
                continue
            emp_id = emp_map.get(emp_code)
            if emp_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "employee_code", "message": f"Employee not found: {emp_code}"})
                continue

            try:
                thr_year = int(float(row.get("thr_year")))
            except (ValueError, TypeError):
                errors.append({"row": row_num, "code": emp_code, "field": "thr_year", "message": "thr_year must be a number"})
                continue

            holiday = ExcelImportService._safe_str(row.get("religious_holiday"))
            if holiday not in VALID_THR_HOLIDAYS:
                errors.append({"row": row_num, "code": emp_code, "field": "religious_holiday", "message": f"Invalid holiday: {holiday}. Must be one of {VALID_THR_HOLIDAYS}"})
                continue

            try:
                amount = float(row.get("amount"))
                if amount < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({"row": row_num, "code": emp_code, "field": "amount", "message": "amount must be a non-negative number"})
                continue

            thr_date = ExcelImportService._parse_date(row.get("thr_date"))
            if not thr_date:
                errors.append({"row": row_num, "code": emp_code, "field": "thr_date", "message": "thr_date is required or invalid format (YYYY-MM-DD)"})
                continue

            basis = ExcelImportService._safe_str(row.get("calculation_basis")) or "BASE_SALARY"
            if basis not in VALID_THR_BASIS:
                errors.append({"row": row_num, "code": emp_code, "field": "calculation_basis", "message": f"Invalid basis: {basis}. Must be one of {VALID_THR_BASIS}"})
                continue

            valid_records.append(THRRecord(
                company_id=company_id,
                employee_id=emp_id,
                thr_year=thr_year,
                religious_holiday=holiday,
                amount=amount,
                thr_date=thr_date,
                calculation_basis=basis,
                tenure_months=0,
                description=ExcelImportService._safe_str(row.get("description")),
            ))

        if valid_records:
            for i in range(0, len(valid_records), 50):
                db.add_all(valid_records[i:i + 50])
                db.flush()
            db.commit()

        result = {
            "total_rows": total_rows,
            "success_count": len(valid_records),
            "error_count": len(errors),
            "errors": [{"row": e["row"], "field": e.get("field"), "message": e["message"]} for e in errors],
        }
        error_bytes = ExcelImportService._generate_error_report(errors) if errors else None
        return result, error_bytes

    @staticmethod
    def import_reimbursements(file_bytes: bytes, company_id: int, db: Session) -> tuple[dict, Optional[bytes]]:
        """Bulk import reimbursement claims from Excel file."""
        df = pd.read_excel(BytesIO(file_bytes))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        emp_map = {
            row.employee_code: row.id
            for row in db.query(Employee.id, Employee.employee_code).filter(
                Employee.company_id == company_id
            ).all()
        }
        type_map = {
            row.code: row.id
            for row in db.query(ReimbursementType.id, ReimbursementType.code).filter(
                ReimbursementType.company_id == company_id
            ).all()
        }

        errors = []
        valid_records = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2
            emp_code = ExcelImportService._safe_str(row.get("employee_code"))
            type_code = ExcelImportService._safe_str(row.get("reimbursement_type_code"))

            if not emp_code:
                errors.append({"row": row_num, "code": "", "field": "employee_code", "message": "employee_code is required"})
                continue
            emp_id = emp_map.get(emp_code)
            if emp_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "employee_code", "message": f"Employee not found: {emp_code}"})
                continue

            if not type_code:
                errors.append({"row": row_num, "code": emp_code, "field": "reimbursement_type_code", "message": "reimbursement_type_code is required"})
                continue
            type_id = type_map.get(type_code)
            if type_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "reimbursement_type_code", "message": f"Reimbursement type not found: {type_code}"})
                continue

            try:
                amount = float(row.get("claim_amount"))
                if amount <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({"row": row_num, "code": emp_code, "field": "claim_amount", "message": "claim_amount must be a positive number"})
                continue

            claim_date = ExcelImportService._parse_date(row.get("claim_date"))
            if not claim_date:
                errors.append({"row": row_num, "code": emp_code, "field": "claim_date", "message": "claim_date is required or invalid format (YYYY-MM-DD)"})
                continue

            expense_date = ExcelImportService._parse_date(row.get("expense_date")) or claim_date

            status = ExcelImportService._safe_str(row.get("approval_status")) or "PENDING"
            if status not in VALID_REIMBURSEMENT_STATUS:
                errors.append({"row": row_num, "code": emp_code, "field": "approval_status", "message": f"Invalid status: {status}"})
                continue

            approved_amount = None
            if "approved_amount" in df.columns:
                try:
                    approved_amount = float(row.get("approved_amount")) if row.get("approved_amount") is not None else None
                except (ValueError, TypeError):
                    pass

            valid_records.append(Reimbursement(
                employee_id=emp_id,
                reimbursement_type_id=type_id,
                claim_amount=amount,
                approved_amount=approved_amount,
                claim_date=claim_date,
                expense_date=expense_date,
                description=ExcelImportService._safe_str(row.get("description")),
                approval_status=status,
            ))

        if valid_records:
            for i in range(0, len(valid_records), 50):
                db.add_all(valid_records[i:i + 50])
                db.flush()
            db.commit()

        result = {
            "total_rows": total_rows,
            "success_count": len(valid_records),
            "error_count": len(errors),
            "errors": [{"row": e["row"], "field": e.get("field"), "message": e["message"]} for e in errors],
        }
        error_bytes = ExcelImportService._generate_error_report(errors) if errors else None
        return result, error_bytes

    @staticmethod
    def import_kasbon(file_bytes: bytes, company_id: int, db: Session) -> tuple[dict, Optional[bytes]]:
        """Bulk import kasbon/loan records from Excel file."""
        df = pd.read_excel(BytesIO(file_bytes))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        emp_map = {
            row.employee_code: row.id
            for row in db.query(Employee.id, Employee.employee_code).filter(
                Employee.company_id == company_id
            ).all()
        }

        errors = []
        valid_records = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2
            emp_code = ExcelImportService._safe_str(row.get("employee_code"))

            if not emp_code:
                errors.append({"row": row_num, "code": "", "field": "employee_code", "message": "employee_code is required"})
                continue
            emp_id = emp_map.get(emp_code)
            if emp_id is None:
                errors.append({"row": row_num, "code": emp_code, "field": "employee_code", "message": f"Employee not found: {emp_code}"})
                continue

            kasbon_number = ExcelImportService._safe_str(row.get("kasbon_number"))
            if not kasbon_number:
                errors.append({"row": row_num, "code": emp_code, "field": "kasbon_number", "message": "kasbon_number is required"})
                continue

            existing = db.query(KasbonRequest).filter(KasbonRequest.kasbon_number == kasbon_number).first()
            if existing:
                errors.append({"row": row_num, "code": emp_code, "field": "kasbon_number", "message": f"Kasbon number already exists: {kasbon_number}"})
                continue

            try:
                principal = float(row.get("principal_amount"))
                if principal <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({"row": row_num, "code": emp_code, "field": "principal_amount", "message": "principal_amount must be a positive number"})
                continue

            try:
                interest_rate = float(row.get("interest_rate")) if row.get("interest_rate") is not None else 0
                if interest_rate < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({"row": row_num, "code": emp_code, "field": "interest_rate", "message": "interest_rate must be a non-negative number"})
                continue

            try:
                installments = int(float(row.get("number_of_installments")))
                if installments <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({"row": row_num, "code": emp_code, "field": "number_of_installments", "message": "number_of_installments must be a positive integer"})
                continue

            request_date = ExcelImportService._parse_date(row.get("request_date"))
            if not request_date:
                errors.append({"row": row_num, "code": emp_code, "field": "request_date", "message": "request_date is required or invalid format (YYYY-MM-DD)"})
                continue

            purpose = ExcelImportService._safe_str(row.get("purpose"))
            if not purpose:
                errors.append({"row": row_num, "code": emp_code, "field": "purpose", "message": "purpose is required"})
                continue

            status = ExcelImportService._safe_str(row.get("status")) or "PENDING"
            if status not in VALID_KASBON_STATUS:
                errors.append({"row": row_num, "code": emp_code, "field": "status", "message": f"Invalid status: {status}"})
                continue

            total = principal * (1 + interest_rate / 100)
            installment_amount = round(total / installments, 2)

            valid_records.append(KasbonRequest(
                employee_id=emp_id,
                kasbon_number=kasbon_number,
                principal_amount=principal,
                interest_rate=interest_rate,
                number_of_installments=installments,
                installment_amount=installment_amount,
                request_date=request_date,
                purpose=purpose,
                status=status,
            ))

        if valid_records:
            for i in range(0, len(valid_records), 50):
                db.add_all(valid_records[i:i + 50])
                db.flush()
            db.commit()

        result = {
            "total_rows": total_rows,
            "success_count": len(valid_records),
            "error_count": len(errors),
            "errors": [{"row": e["row"], "field": e.get("field"), "message": e["message"]} for e in errors],
        }
        error_bytes = ExcelImportService._generate_error_report(errors) if errors else None
        return result, error_bytes
