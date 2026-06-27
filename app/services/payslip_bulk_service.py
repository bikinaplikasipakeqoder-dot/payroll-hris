"""Service for bulk payslip PDF generation with background job tracking."""

import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.payroll import (
    Payslip,
    PayrollRun,
    PayslipTemplate,
    PayslipRecord,
    PayslipGenerationJob,
)
from app.models.employee import Employee, Department, Position
from app.models.auth import Company
from app.models.integration import Notification
from app.services.payslip_pdf_service import PayslipPdfService


class PayslipBulkService:
    """Service for managing bulk payslip PDF generation."""

    BULK_STORAGE_BASE = Path("storage/payslips/bulk")

    @staticmethod
    def start_bulk_generation(payroll_run_id: int, company_id: int, db: Session) -> str:
        """Create a new bulk generation job. Returns job_id UUID string."""
        # Count payslips in the payroll run
        total_count = (
            db.query(Payslip)
            .filter(Payslip.payroll_run_id == payroll_run_id)
            .count()
        )
        if total_count == 0:
            raise ValueError("No payslips found for this payroll run")

        job_id = str(uuid.uuid4())
        job = PayslipGenerationJob(
            job_id=job_id,
            company_id=company_id,
            payroll_run_id=payroll_run_id,
            total_count=total_count,
            completed_count=0,
            failed_count=0,
            status="QUEUED",
        )
        db.add(job)
        db.commit()
        return job_id

    @staticmethod
    def _render_single(
        payslip: Payslip,
        employee: Employee,
        company: Company,
        department_name: str,
        position_name: str,
        template_html: str,
        css: Optional[str],
        year: int,
        month: int,
    ) -> Tuple[str, Optional[bytes]]:
        """Render a single payslip PDF. Returns (filename, pdf_bytes) or (filename, None) on error."""
        try:
            # Temporarily attach payroll_run info for period label
            period_str = f"{year}-{month:02d}"
            filename = f"{employee.employee_code}_{period_str}.pdf"

            html = PayslipPdfService.render_html(
                payslip=payslip,
                employee=employee,
                company=company,
                department_name=department_name,
                position_name=position_name,
                template_html=template_html,
                css=css,
            )
            pdf_bytes = PayslipPdfService.generate_pdf(html)
            return filename, pdf_bytes
        except Exception:
            period_str = f"{year}-{month:02d}"
            filename = f"{employee.employee_code}_{period_str}.pdf" if employee else "unknown.pdf"
            return filename, None

    @staticmethod
    def process_bulk_job(job_id: str):
        """Background task: Generate all PDFs for a bulk job. Uses its own DB session."""
        db = SessionLocal()
        try:
            # 1. Load job, update status to PROCESSING
            job = (
                db.query(PayslipGenerationJob)
                .filter(PayslipGenerationJob.job_id == job_id)
                .first()
            )
            if not job:
                return

            job.status = "PROCESSING"
            job.started_at = datetime.now()
            db.commit()

            # 2. Load payroll run
            payroll_run = (
                db.query(PayrollRun)
                .filter(PayrollRun.id == job.payroll_run_id)
                .first()
            )
            if not payroll_run:
                job.status = "FAILED"
                job.error_message = "Payroll run not found"
                job.completed_at = datetime.now()
                db.commit()
                return

            # Parse year/month from payroll_period
            try:
                parts = payroll_run.payroll_period.split("-")
                year = int(parts[0])
                month = int(parts[1])
            except (IndexError, ValueError):
                job.status = "FAILED"
                job.error_message = f"Invalid payroll_period format: {payroll_run.payroll_period}"
                job.completed_at = datetime.now()
                db.commit()
                return

            # 3. Load all payslips for this run
            payslips = (
                db.query(Payslip)
                .filter(Payslip.payroll_run_id == payroll_run.id)
                .all()
            )

            # Load all employees
            employee_ids = [p.employee_id for p in payslips]
            employees = {
                e.id: e
                for e in db.query(Employee).filter(Employee.id.in_(employee_ids)).all()
            } if employee_ids else {}

            # Load departments and positions
            dept_ids = list(set(e.department_id for e in employees.values() if e.department_id))
            departments = {
                d.id: d.name
                for d in db.query(Department).filter(Department.id.in_(dept_ids)).all()
            } if dept_ids else {}

            pos_ids = list(set(e.position_id for e in employees.values() if e.position_id))
            positions = {
                p.id: p.name
                for p in db.query(Position).filter(Position.id.in_(pos_ids)).all()
            } if pos_ids else {}

            # 4. Load company and template
            company = db.query(Company).filter(Company.id == job.company_id).first()
            if not company:
                company = Company(name="", address="", phone="", email="")

            template_record = (
                db.query(PayslipTemplate)
                .filter(
                    PayslipTemplate.company_id == job.company_id,
                    PayslipTemplate.is_active == True,
                    PayslipTemplate.is_default == True,
                )
                .first()
            )
            if template_record:
                template_html = template_record.html_content
                css = template_record.css_content
            else:
                template_html = PayslipPdfService.get_default_template()
                css = None

            # Attach payroll_run to each payslip for period label resolution
            for ps in payslips:
                ps.payroll_run = payroll_run

            # 5. Generate PDFs using ThreadPoolExecutor
            pdf_files: List[Tuple[str, bytes]] = []
            completed_count = 0
            failed_count = 0

            # Ensure storage directory exists
            storage_dir = PayslipPdfService.ensure_storage_dir(year, month)

            # Prepare rendering tasks
            render_tasks = []
            for ps in payslips:
                emp = employees.get(ps.employee_id)
                if not emp:
                    failed_count += 1
                    continue
                dept_name = departments.get(emp.department_id, "") if emp.department_id else ""
                pos_name = positions.get(emp.position_id, "") if emp.position_id else ""
                render_tasks.append((ps, emp, company, dept_name, pos_name, template_html, css, year, month))

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(
                        PayslipBulkService._render_single,
                        task[0], task[1], task[2], task[3],
                        task[4], task[5], task[6], task[7], task[8],
                    ): task
                    for task in render_tasks
                }

                batch_counter = 0
                for future in as_completed(futures):
                    task_data = futures[future]
                    ps = task_data[0]
                    emp = task_data[1]

                    try:
                        filename, pdf_bytes = future.result()
                    except Exception:
                        failed_count += 1
                        batch_counter += 1
                        continue

                    if pdf_bytes is None:
                        failed_count += 1
                    else:
                        completed_count += 1
                        pdf_files.append((filename, pdf_bytes))

                        # Save individual PDF to disk
                        file_path = storage_dir / filename
                        file_path.write_bytes(pdf_bytes)

                        # Create PayslipRecord
                        existing_record = (
                            db.query(PayslipRecord)
                            .filter(
                                PayslipRecord.employee_id == emp.id,
                                PayslipRecord.year == year,
                                PayslipRecord.month == month,
                            )
                            .first()
                        )
                        if existing_record:
                            existing_record.file_path = str(file_path)
                            existing_record.file_size_bytes = len(pdf_bytes)
                            existing_record.generated_at = datetime.now()
                            existing_record.status = "COMPLETED"
                            existing_record.payslip_id = ps.id
                        else:
                            record = PayslipRecord(
                                payslip_id=ps.id,
                                employee_id=emp.id,
                                company_id=job.company_id,
                                year=year,
                                month=month,
                                file_path=str(file_path),
                                file_size_bytes=len(pdf_bytes),
                                generated_at=datetime.now(),
                                status="COMPLETED",
                            )
                            db.add(record)

                    batch_counter += 1

                    # Update progress every 10 items
                    if batch_counter % 10 == 0:
                        job.completed_count = completed_count
                        job.failed_count = failed_count
                        db.commit()

            # 6. Create ZIP of all PDFs
            zip_path = ""
            if pdf_files:
                zip_path = PayslipBulkService.create_zip(pdf_files, job_id)

            # 7. Update job status
            job.completed_count = completed_count
            job.failed_count = failed_count
            job.status = "COMPLETED"
            job.result_file_path = zip_path
            job.completed_at = datetime.now()

            # 8. Create Notification
            notification = Notification(
                company_id=job.company_id,
                notification_type="BULK_COMPLETE",
                title="Bulk payslip generation complete",
                message=(
                    f"Berhasil generate {completed_count} dari {job.total_count} slip gaji. "
                    f"Gagal: {failed_count}."
                ),
                link=zip_path if zip_path else None,
            )
            db.add(notification)
            db.commit()

        except Exception as e:
            # Mark job as FAILED
            db.rollback()
            try:
                job = (
                    db.query(PayslipGenerationJob)
                    .filter(PayslipGenerationJob.job_id == job_id)
                    .first()
                )
                if job:
                    job.status = "FAILED"
                    job.error_message = str(e)[:1000]
                    job.completed_at = datetime.now()
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    @staticmethod
    def get_job_status(job_id: str, db: Session) -> Optional[PayslipGenerationJob]:
        """Query job status by job_id."""
        return (
            db.query(PayslipGenerationJob)
            .filter(PayslipGenerationJob.job_id == job_id)
            .first()
        )

    @staticmethod
    def create_zip(pdf_files: List[Tuple[str, bytes]], job_id: str) -> str:
        """Create ZIP file from list of (filename, pdf_bytes). Returns file path."""
        zip_dir = PayslipBulkService.BULK_STORAGE_BASE
        zip_dir.mkdir(parents=True, exist_ok=True)

        zip_filename = f"{job_id}.zip"
        zip_path = zip_dir / zip_filename

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, pdf_bytes in pdf_files:
                zf.writestr(filename, pdf_bytes)

        return str(zip_path)
