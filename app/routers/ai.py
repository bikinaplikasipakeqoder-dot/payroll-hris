"""
AI module endpoints — settings, chat, and reports.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.integration import AiSetting
from app.schemas.ai import (
    AiSettingCreate, AiSettingUpdate, AiSettingResponse,
    AiChatRequest, AiChatResponse,
    AiReportRequest, AiReportResponse,
    AiTestConnectionRequest, AiTestConnectionResponse,
)
from app.services.ai_proxy_service import (
    get_ai_settings, mask_api_key, call_ai, test_connection, build_context_prompt,
)

router = APIRouter(prefix="/ai", tags=["AI"])


# --- Settings Endpoints ---

@router.get("/settings", response_model=AiSettingResponse)
def get_settings(company_id: int = Query(...), db: Session = Depends(get_db)):
    """Get AI settings for a company (API key masked)."""
    setting = get_ai_settings(company_id, db)
    return AiSettingResponse(
        id=setting.id,
        company_id=setting.company_id,
        provider_name=setting.provider_name,
        api_key_masked=mask_api_key(setting.api_key),
        api_host=setting.api_host,
        model_name=setting.model_name,
        system_prompt=setting.system_prompt,
        temperature=setting.temperature,
        max_tokens=setting.max_tokens,
        is_active=setting.is_active,
        created_at=setting.created_at,
        updated_at=setting.updated_at,
    )


@router.post("/settings", response_model=AiSettingResponse, status_code=status.HTTP_201_CREATED)
def create_settings(payload: AiSettingCreate, db: Session = Depends(get_db)):
    """Create AI settings for a company."""
    # Check if settings already exist
    existing = db.query(AiSetting).filter(AiSetting.company_id == payload.company_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="AI settings already exist for this company. Use PATCH to update.")

    setting = AiSetting(
        company_id=payload.company_id,
        provider_name=payload.provider_name,
        api_key=payload.api_key,
        api_host=payload.api_host,
        model_name=payload.model_name,
        system_prompt=payload.system_prompt,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        is_active=payload.is_active,
    )
    db.add(setting)
    db.commit()
    db.refresh(setting)

    return AiSettingResponse(
        id=setting.id, company_id=setting.company_id,
        provider_name=setting.provider_name,
        api_key_masked=mask_api_key(setting.api_key),
        api_host=setting.api_host, model_name=setting.model_name,
        system_prompt=setting.system_prompt, temperature=setting.temperature,
        max_tokens=setting.max_tokens, is_active=setting.is_active,
        created_at=setting.created_at, updated_at=setting.updated_at,
    )


@router.patch("/settings/{setting_id}", response_model=AiSettingResponse)
def update_settings(setting_id: int, payload: AiSettingUpdate, db: Session = Depends(get_db)):
    """Update AI settings."""
    setting = db.query(AiSetting).filter(AiSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="AI settings not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)

    db.commit()
    db.refresh(setting)

    return AiSettingResponse(
        id=setting.id, company_id=setting.company_id,
        provider_name=setting.provider_name,
        api_key_masked=mask_api_key(setting.api_key),
        api_host=setting.api_host, model_name=setting.model_name,
        system_prompt=setting.system_prompt, temperature=setting.temperature,
        max_tokens=setting.max_tokens, is_active=setting.is_active,
        created_at=setting.created_at, updated_at=setting.updated_at,
    )


# --- Test Connection ---

@router.post("/test-connection", response_model=AiTestConnectionResponse)
def test_ai_connection(payload: AiTestConnectionRequest, db: Session = Depends(get_db)):
    """Test connectivity to the configured AI provider."""
    setting = get_ai_settings(payload.company_id, db)
    result = test_connection(setting)
    return AiTestConnectionResponse(**result)


# --- Chat Endpoint ---

@router.post("/chat", response_model=AiChatResponse)
def chat_with_ai(payload: AiChatRequest, db: Session = Depends(get_db)):
    """Send a message to the AI assistant with optional context."""
    setting = get_ai_settings(payload.company_id, db)

    # Build messages array
    system_content = build_context_prompt(payload.context_type, payload.company_id, db)
    if setting.system_prompt:
        system_content = setting.system_prompt + "\n\n" + system_content

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": payload.message},
    ]

    response = call_ai(setting, messages)

    # Extract assistant response
    choice = response.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "Maaf, tidak ada respons dari AI.")
    tokens = response.get("usage", {}).get("total_tokens")

    return AiChatResponse(role="assistant", content=content, tokens_used=tokens)


# --- Reports Endpoint ---

@router.post("/reports", response_model=AiReportResponse)
def generate_report(payload: AiReportRequest, db: Session = Depends(get_db)):
    """Generate an AI-powered report."""
    from datetime import datetime as dt

    setting = get_ai_settings(payload.company_id, db)

    # Build report-specific prompt
    report_prompts = {
        "payroll_summary": "Buat ringkasan payroll yang komprehensif",
        "overtime_analysis": "Analisis tren dan pola lembur karyawan",
        "tax_compliance": "Review kepatuhan pajak PPh 21 dan identifikasi potensi masalah",
        "employee_insights": "Berikan insight dan analisis dari data karyawan",
    }

    report_titles = {
        "payroll_summary": "Ringkasan Payroll",
        "overtime_analysis": "Analisis Lembur",
        "tax_compliance": "Review Kepatuhan Pajak",
        "employee_insights": "Insight Karyawan",
    }

    base_prompt = report_prompts[payload.report_type]
    if payload.period_month and payload.period_year:
        base_prompt += f" untuk bulan {payload.period_month}/{payload.period_year}"

    # Get context data for the report
    context = build_context_prompt(
        "payroll" if payload.report_type == "payroll_summary" else
        "employee" if payload.report_type in ("employee_insights", "overtime_analysis") else
        "tax",
        payload.company_id, db
    )

    messages = [
        {"role": "system", "content": f"Kamu adalah AI analis HR/Payroll Indonesia. Berikan laporan dalam format markdown yang rapi. Berikut data konteks:\n\n{context}"},
        {"role": "user", "content": base_prompt},
    ]

    response = call_ai(setting, messages, max_tokens=setting.max_tokens)

    choice = response.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "Gagal menghasilkan laporan.")

    title = report_titles[payload.report_type]
    if payload.period_month and payload.period_year:
        month_names = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        title += f" — {month_names[payload.period_month]} {payload.period_year}"

    return AiReportResponse(
        report_title=title,
        report_content=content,
        generated_at=dt.now(),
        model_used=setting.model_name,
    )
