"""Service for generating payslip PDFs using WeasyPrint and Jinja2 templates."""

import json
from io import BytesIO
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple

from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

from app.models.payroll import Payslip, PayrollRun, PayslipTemplate, PayslipRecord
from app.models.employee import Employee, Department, Position
from app.models.auth import Company


def format_idr(value) -> str:
    """Format a numeric value as Indonesian Rupiah: Rp 12,345,678."""
    if value is None:
        return "Rp 0"
    if isinstance(value, Decimal):
        value = int(value)
    else:
        value = int(float(value))
    formatted = f"{value:,.0f}".replace(",", ".")
    return f"Rp {formatted}"


MONTH_NAMES_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


class PayslipPdfService:
    """Service for rendering payslip PDFs."""

    STORAGE_BASE = Path("storage/payslips")

    @staticmethod
    def get_default_template() -> str:
        """Return the default HTML+CSS payslip template with Jinja2 variables."""
        return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {
    size: A4;
    margin: 15mm 20mm;
}
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 10pt;
    color: #1f2937;
    line-height: 1.4;
}
.header {
    text-align: center;
    border-bottom: 3px solid #2563EB;
    padding-bottom: 12px;
    margin-bottom: 16px;
}
.header h1 {
    font-size: 16pt;
    color: #2563EB;
    margin-bottom: 4px;
}
.header p {
    font-size: 9pt;
    color: #6b7280;
}
.period-label {
    text-align: center;
    font-size: 12pt;
    font-weight: bold;
    color: #374151;
    margin-bottom: 16px;
    padding: 8px;
    background: #eff6ff;
    border-radius: 4px;
}
.employee-info {
    margin-bottom: 16px;
}
.employee-info table {
    width: 100%;
    border-collapse: collapse;
}
.employee-info td {
    padding: 3px 8px;
    font-size: 9pt;
}
.employee-info td.label {
    width: 150px;
    font-weight: 600;
    color: #4b5563;
}
.section-header {
    background: #f3f4f6;
    padding: 6px 10px;
    font-weight: 700;
    font-size: 10pt;
    color: #1f2937;
    border-left: 4px solid #2563EB;
    margin: 12px 0 8px 0;
}
table.detail {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 8px;
}
table.detail th {
    background: #2563EB;
    color: white;
    padding: 6px 10px;
    text-align: left;
    font-size: 9pt;
}
table.detail td {
    padding: 5px 10px;
    border-bottom: 1px solid #e5e7eb;
    font-size: 9pt;
}
table.detail tr:last-child td {
    border-bottom: none;
}
table.detail td.amount {
    text-align: right;
    font-family: 'Courier New', monospace;
}
.subtotal td {
    font-weight: 700;
    border-top: 2px solid #d1d5db;
    padding-top: 8px;
}
.net-pay {
    margin-top: 20px;
    padding: 14px;
    background: #2563EB;
    color: white;
    text-align: center;
    border-radius: 6px;
}
.net-pay .label {
    font-size: 10pt;
    font-weight: 600;
    margin-bottom: 4px;
}
.net-pay .amount {
    font-size: 18pt;
    font-weight: 800;
    letter-spacing: 0.5px;
}
.footer {
    margin-top: 30px;
    padding-top: 10px;
    border-top: 1px solid #e5e7eb;
    text-align: center;
    font-size: 8pt;
    color: #9ca3af;
}
</style>
</head>
<body>
    <div class="header">
        <h1>{{ company.name or 'Perusahaan' }}</h1>
        <p>{{ company.address or '' }}</p>
        <p>{{ company.phone or '' }} | {{ company.email or '' }}</p>
    </div>

    <div class="period-label">SLIP GAJI - {{ period_label }}</div>

    <div class="employee-info">
        <table>
            <tr>
                <td class="label">Kode Karyawan</td>
                <td>: {{ employee.employee_code or '-' }}</td>
                <td class="label">Departemen</td>
                <td>: {{ department_name or '-' }}</td>
            </tr>
            <tr>
                <td class="label">Nama</td>
                <td>: {{ employee.full_name or '-' }}</td>
                <td class="label">Jabatan</td>
                <td>: {{ position_name or '-' }}</td>
            </tr>
            <tr>
                <td class="label">NPWP</td>
                <td>: {{ employee.npwp or '-' }}</td>
                <td class="label">Status PTKP</td>
                <td>: {{ employee.ptkp_status or '-' }}</td>
            </tr>
            <tr>
                <td class="label">Bank</td>
                <td colspan="3">: {{ employee.bank_name or '-' }} - {{ employee.bank_account_number or '-' }}</td>
            </tr>
        </table>
    </div>

    <div class="section-header">PENGHASILAN</div>
    <table class="detail">
        <tr>
            <th style="width:60%">Komponen</th>
            <th style="width:40%; text-align:right">Jumlah</th>
        </tr>
        <tr>
            <td>Gaji Pokok</td>
            <td class="amount">{{ payslip.basic_salary | format_idr }}</td>
        </tr>
        <tr>
            <td>Tunjangan</td>
            <td class="amount">{{ payslip.total_allowances | format_idr }}</td>
        </tr>
        {% for item in allowance_items %}
        <tr>
            <td style="padding-left:30px; color:#6b7280;">- {{ item.name }}</td>
            <td class="amount" style="color:#6b7280;">{{ item.amount | format_idr }}</td>
        </tr>
        {% endfor %}
        <tr>
            <td>Lembur</td>
            <td class="amount">{{ payslip.overtime_amount | format_idr }}</td>
        </tr>
        <tr>
            <td>Bonus</td>
            <td class="amount">{{ payslip.bonus_amount | format_idr }}</td>
        </tr>
        <tr class="subtotal">
            <td><strong>Penghasilan Kotor</strong></td>
            <td class="amount"><strong>{{ payslip.gross_salary | format_idr }}</strong></td>
        </tr>
    </table>

    <div class="section-header">POTONGAN</div>
    <table class="detail">
        <tr>
            <th style="width:60%">Komponen</th>
            <th style="width:40%; text-align:right">Jumlah</th>
        </tr>
        <tr>
            <td>PPh 21</td>
            <td class="amount">{{ payslip.pph21_tax | format_idr }}</td>
        </tr>
        <tr>
            <td>BPJS Kesehatan</td>
            <td class="amount">{{ payslip.bpjs_kes_employee | format_idr }}</td>
        </tr>
        <tr>
            <td>BPJS JHT</td>
            <td class="amount">{{ payslip.bpjs_jht_employee | format_idr }}</td>
        </tr>
        <tr>
            <td>BPJS JP</td>
            <td class="amount">{{ payslip.bpjs_jp_employee | format_idr }}</td>
        </tr>
        <tr>
            <td>Kasbon</td>
            <td class="amount">{{ payslip.kasbon_deduction | format_idr }}</td>
        </tr>
        <tr>
            <td>Potongan Lain</td>
            <td class="amount">{{ payslip.other_deductions | format_idr }}</td>
        </tr>
        {% for item in deduction_items %}
        <tr>
            <td style="padding-left:30px; color:#6b7280;">- {{ item.name }}</td>
            <td class="amount" style="color:#6b7280;">{{ item.amount | format_idr }}</td>
        </tr>
        {% endfor %}
        <tr class="subtotal">
            <td><strong>Total Potongan</strong></td>
            <td class="amount"><strong>{{ payslip.total_deductions | format_idr }}</strong></td>
        </tr>
    </table>

    <div class="net-pay">
        <div class="label">GAJI BERSIH (Take Home Pay)</div>
        <div class="amount">{{ payslip.net_salary | format_idr }}</div>
    </div>

    <div class="footer">
        <p>Digenerate pada: {{ generated_at }} | Dokumen ini digenerate secara otomatis oleh sistem payroll.</p>
    </div>
</body>
</html>"""

    @staticmethod
    def render_html(
        payslip: Payslip,
        employee: Employee,
        company: Company,
        department_name: str,
        position_name: str,
        template_html: str,
        css: Optional[str] = None,
    ) -> str:
        """Render Jinja2 template with payslip/employee/company context."""
        # Parse allowances_detail and deductions_detail JSON
        allowance_items = []
        if payslip.allowances_detail:
            try:
                raw = json.loads(payslip.allowances_detail)
                if isinstance(raw, list):
                    allowance_items = raw
                elif isinstance(raw, dict):
                    allowance_items = [
                        {"name": k, "amount": v} for k, v in raw.items()
                    ]
            except (json.JSONDecodeError, TypeError):
                pass

        deduction_items = []
        if payslip.deductions_detail:
            try:
                raw = json.loads(payslip.deductions_detail)
                if isinstance(raw, list):
                    deduction_items = raw
                elif isinstance(raw, dict):
                    deduction_items = [
                        {"name": k, "amount": v} for k, v in raw.items()
                    ]
            except (json.JSONDecodeError, TypeError):
                pass

        # Determine period label
        period_label = ""
        if hasattr(payslip, "payroll_run") and payslip.payroll_run:
            period_str = payslip.payroll_run.payroll_period  # "YYYY-MM"
            try:
                parts = period_str.split("-")
                year = int(parts[0])
                month = int(parts[1])
                period_label = f"{MONTH_NAMES_ID[month]} {year}"
            except (IndexError, ValueError):
                period_label = period_str
        else:
            period_label = ""

        # Build Jinja2 environment with format_idr filter
        env = Environment(loader=BaseLoader())
        env.filters["format_idr"] = format_idr

        # If custom CSS provided, inject into template
        if css:
            template_html = template_html.replace(
                "</style>", f"\n{css}\n</style>"
            )

        template = env.from_string(template_html)

        context = {
            "payslip": payslip,
            "employee": employee,
            "company": company,
            "department_name": department_name or "-",
            "position_name": position_name or "-",
            "period_label": period_label,
            "allowance_items": allowance_items,
            "deduction_items": deduction_items,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }

        return template.render(**context)

    @staticmethod
    def generate_pdf(html: str) -> bytes:
        """Convert rendered HTML to PDF bytes using WeasyPrint."""
        from weasyprint import HTML  # lazy import to avoid blocking startup
        pdf_bytes = HTML(string=html).write_pdf()
        return pdf_bytes

    @staticmethod
    def ensure_storage_dir(year: int, month: int) -> Path:
        """Create storage directory if not exists, return Path."""
        dir_path = PayslipPdfService.STORAGE_BASE / str(year) / f"{month:02d}"
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @staticmethod
    def generate_single_payslip(
        employee_id: int, year: int, month: int, db: Session
    ) -> Tuple[bytes, str]:
        """Generate a single payslip PDF for an employee/period. Returns (pdf_bytes, filename)."""
        period_str = f"{year}-{month:02d}"

        # 1. Find PayrollRun for the period
        payroll_run = (
            db.query(PayrollRun)
            .filter(PayrollRun.payroll_period.like(f"{period_str}%"))
            .first()
        )
        if not payroll_run:
            raise ValueError(f"No payroll run found for period {period_str}")

        # 2. Find Payslip for this employee in that run
        payslip = (
            db.query(Payslip)
            .filter(
                Payslip.payroll_run_id == payroll_run.id,
                Payslip.employee_id == employee_id,
            )
            .first()
        )
        if not payslip:
            raise ValueError(
                f"No payslip found for employee {employee_id} in period {period_str}"
            )

        # Attach payroll_run reference for period_label resolution
        payslip.payroll_run = payroll_run

        # 3. Load Employee with department/position
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        department_name = ""
        if employee.department_id:
            dept = db.query(Department).filter(Department.id == employee.department_id).first()
            department_name = dept.name if dept else ""

        position_name = ""
        if employee.position_id:
            pos = db.query(Position).filter(Position.id == employee.position_id).first()
            position_name = pos.name if pos else ""

        # 4. Load Company
        company = db.query(Company).filter(Company.id == employee.company_id).first()
        if not company:
            company = Company(name="", address="", phone="", email="")

        # 5. Get active template (or default)
        template_record = (
            db.query(PayslipTemplate)
            .filter(
                PayslipTemplate.company_id == employee.company_id,
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

        # 6. Render HTML → Generate PDF
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

        # 7. Save to disk
        dir_path = PayslipPdfService.ensure_storage_dir(year, month)
        filename = f"{employee.employee_code}_{period_str}.pdf"
        file_path = dir_path / filename
        file_path.write_bytes(pdf_bytes)

        # 8. Create/update PayslipRecord in DB
        existing_record = (
            db.query(PayslipRecord)
            .filter(
                PayslipRecord.employee_id == employee_id,
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
            existing_record.payslip_id = payslip.id
        else:
            record = PayslipRecord(
                payslip_id=payslip.id,
                employee_id=employee_id,
                company_id=employee.company_id,
                year=year,
                month=month,
                file_path=str(file_path),
                file_size_bytes=len(pdf_bytes),
                generated_at=datetime.now(),
                status="COMPLETED",
            )
            db.add(record)

        db.commit()

        # 9. Return (pdf_bytes, filename)
        return pdf_bytes, filename
