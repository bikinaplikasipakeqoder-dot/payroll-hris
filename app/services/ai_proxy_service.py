"""
AI Proxy Service — handles communication with OpenAI-compatible AI providers.

Provides:
- Settings retrieval with validation
- API key masking
- Synchronous AI chat completion calls via httpx
- Connection testing
- Context-aware prompt building for payroll/HR domain
"""

import logging
import time
from typing import Optional

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.integration import AiSetting
from app.models.payroll import PayrollRun
from app.models.employee import Employee, Department
from app.models.tax import TaxSetting
from app.models.bpjs import BpjsSetting


def get_ai_settings(company_id: int, db: Session) -> AiSetting:
    """
    Retrieve active AI settings for a company.
    Raises HTTPException 404 if not found or inactive.
    """
    setting = (
        db.query(AiSetting)
        .filter(AiSetting.company_id == company_id, AiSetting.is_active == True)
        .first()
    )
    if not setting:
        raise HTTPException(
            status_code=404,
            detail=f"No active AI settings found for company_id={company_id}. "
                   "Please configure AI settings first.",
        )
    return setting


def mask_api_key(key: Optional[str]) -> Optional[str]:
    """Mask an API key, showing only the last 4 characters."""
    if not key:
        return None
    if len(key) <= 4:
        return "••••••"
    return "••••••" + key[-4:]


def _normalize_api_host(api_host: Optional[str]) -> str:
    """Normalize api_host so /chat/completions is appended correctly."""
    if not api_host:
        return ""
    host = api_host.strip().rstrip("/")
    return host


def call_ai(settings: AiSetting, messages: list[dict], max_tokens: Optional[int] = None) -> dict:
    """
    Call the AI provider's chat completions endpoint (OpenAI-compatible).

    Uses httpx sync client to POST to {api_host}/chat/completions.
    Timeout is configurable per setting (default 9s to fit Vercel Hobby limit).
    Raises appropriate HTTPExceptions on failure.
    """
    host = _normalize_api_host(settings.api_host)
    if not host:
        raise HTTPException(
            status_code=400,
            detail="AI api_host is not configured.",
        )

    url = f"{host}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.model_name,
        "messages": messages,
        "temperature": float(settings.temperature) if settings.temperature else 0.7,
        "max_tokens": max_tokens or settings.max_tokens or 2048,
    }
    timeout = float(settings.timeout_seconds) if settings.timeout_seconds else 9.0
    # Cap timeout to stay under Vercel Hobby serverless limit (10s).
    timeout = min(timeout, 9.0)

    logger.info(
        "Calling AI provider: provider=%s model=%s url=%s timeout=%s messages=%s",
        settings.provider_name,
        settings.model_name,
        url,
        timeout,
        len(messages),
    )

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=body, headers=headers)

        logger.info("AI provider response status: %s", response.status_code)

        if response.status_code >= 400:
            try:
                error_detail = response.json().get("error", {}).get("message", response.text)
            except Exception:
                error_detail = response.text
            raise HTTPException(
                status_code=response.status_code,
                detail=f"AI provider error: {error_detail}",
            )

        return response.json()

    except httpx.TimeoutException:
        logger.warning("AI provider request timed out after %s seconds", timeout)
        raise HTTPException(
            status_code=504,
            detail=f"AI provider request timed out after {timeout} seconds. "
                   "Try increasing timeout in AI settings or use a faster model.",
        )
    except httpx.ConnectError as e:
        logger.warning("Unable to connect to AI provider at %s: %s", url, e)
        raise HTTPException(
            status_code=502,
            detail=f"Unable to connect to AI provider at {url}. Check api_host configuration.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error calling AI provider")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error calling AI provider: {str(e)}",
        )


def test_connection(settings: AiSetting) -> dict:
    """
    Test connectivity to the AI provider.
    Returns a dict with status, message, and latency_ms.
    """
    start = time.time()
    try:
        call_ai(settings, messages=[{"role": "user", "content": "Hi"}], max_tokens=10)
        latency_ms = int((time.time() - start) * 1000)
        return {"status": "ok", "message": "Connected successfully", "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        error_msg = str(e.detail) if hasattr(e, "detail") else str(e)
        return {"status": "error", "message": error_msg, "latency_ms": latency_ms}


def build_context_prompt(context_type: str, company_id: int, db: Session) -> str:
    """
    Build a context-aware system prompt based on the context type.

    Args:
        context_type: One of "general", "payroll", "employee", "tax"
        company_id: The company ID to query context for
        db: Database session

    Returns:
        A system prompt string with relevant context data.
    """
    if context_type == "general":
        return (
            "Kamu adalah asisten AI untuk sistem Payroll & HRIS Indonesia. "
            "Kamu membantu menjawab pertanyaan tentang penggajian, pajak PPh 21, "
            "BPJS, lembur, cuti, dan manajemen karyawan sesuai regulasi Indonesia. "
            "Jawab dalam Bahasa Indonesia yang profesional dan mudah dipahami."
        )

    elif context_type == "payroll":
        runs = (
            db.query(PayrollRun)
            .filter(PayrollRun.company_id == company_id)
            .order_by(PayrollRun.id.desc())
            .limit(3)
            .all()
        )
        if not runs:
            context = "Belum ada data payroll run untuk perusahaan ini."
        else:
            summaries = []
            for run in runs:
                summaries.append(
                    f"- Periode: {run.payroll_period}, Status: {run.status}, "
                    f"Total Karyawan: {run.total_employees}, "
                    f"Total Gross: Rp {run.total_gross:,.0f}, "
                    f"Total Net: Rp {run.total_net:,.0f}, "
                    f"Total Pajak: Rp {run.total_tax:,.0f}"
                )
            context = "Data payroll run terakhir:\n" + "\n".join(summaries)

        return (
            "Kamu adalah asisten AI payroll Indonesia. "
            "Berikut konteks data payroll perusahaan:\n\n"
            f"{context}\n\n"
            "Gunakan data ini untuk menjawab pertanyaan tentang penggajian."
        )

    elif context_type == "employee":
        total = db.query(Employee).filter(Employee.company_id == company_id).count()
        active = (
            db.query(Employee)
            .filter(Employee.company_id == company_id, Employee.is_active == True)
            .count()
        )
        inactive = total - active

        # Department distribution
        dept_counts = (
            db.query(Department.name, db.query(Employee).filter(
                Employee.department_id == Department.id,
                Employee.company_id == company_id,
                Employee.is_active == True,
            ).correlate(Department).count().label("count"))
            .filter(Department.company_id == company_id)
            .all()
        )

        dept_info = ""
        if dept_counts:
            dept_lines = [f"  - {name}: {count} orang" for name, count in dept_counts if count > 0]
            if dept_lines:
                dept_info = "\nDistribusi per departemen:\n" + "\n".join(dept_lines)

        context = (
            f"Total karyawan: {total}\n"
            f"Aktif: {active}, Non-aktif: {inactive}"
            f"{dept_info}"
        )

        return (
            "Kamu adalah asisten AI HR Indonesia. "
            "Berikut konteks data karyawan perusahaan:\n\n"
            f"{context}\n\n"
            "Gunakan data ini untuk menjawab pertanyaan tentang karyawan."
        )

    elif context_type == "tax":
        tax_setting = (
            db.query(TaxSetting)
            .filter(TaxSetting.company_id == company_id)
            .first()
        )
        bpjs_settings = (
            db.query(BpjsSetting)
            .filter(BpjsSetting.company_id == company_id, BpjsSetting.is_active == True)
            .all()
        )

        tax_info = "Belum ada konfigurasi pajak."
        if tax_setting:
            tax_info = f"Metode perhitungan pajak: {tax_setting.tax_calculation_method}"

        bpjs_info = "Belum ada konfigurasi BPJS."
        if bpjs_settings:
            bpjs_lines = []
            for b in bpjs_settings:
                bpjs_lines.append(
                    f"  - {b.bpjs_type}: Karyawan {float(b.employee_rate)*100:.2f}%, "
                    f"Perusahaan {float(b.employer_rate)*100:.2f}%"
                )
            bpjs_info = "Konfigurasi BPJS:\n" + "\n".join(bpjs_lines)

        context = f"{tax_info}\n\n{bpjs_info}"

        return (
            "Kamu adalah asisten AI pajak & BPJS Indonesia. "
            "Berikut konteks konfigurasi pajak perusahaan:\n\n"
            f"{context}\n\n"
            "Gunakan data ini untuk menjawab pertanyaan tentang pajak dan BPJS."
        )

    # Fallback
    return "Kamu adalah asisten AI untuk sistem Payroll & HRIS Indonesia."
