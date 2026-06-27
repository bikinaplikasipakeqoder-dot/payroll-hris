"""
Main FastAPI application for Indonesian Payroll & HRIS system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.routers import (
    payroll_router,
    employees_router,
    tax_router,
    bpjs_router,
    attendance_router,
    ai_router,
    excel_router,
    payslip_router,
    notification_router,
    master_data_router,
    allowances_router,
    deductions_router,
    bonuses_router,
    reimbursements_router,
    kasbon_router,
    thr_router,
    company_entities_router,
    rules_router,
)
from app.middleware.error_handler import register_exception_handlers

app = FastAPI(
    title="Indonesian Payroll & HRIS API",
    description="Enterprise-grade Payroll & HRIS system with PPh 21, BPJS, and Overtime compliance",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
register_exception_handlers(app)

# Register routers under /api/v1 prefix
app.include_router(payroll_router, prefix="/api/v1")
app.include_router(employees_router, prefix="/api/v1")
app.include_router(tax_router, prefix="/api/v1")
app.include_router(bpjs_router, prefix="/api/v1")
app.include_router(attendance_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(excel_router, prefix="/api/v1")
app.include_router(payslip_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(master_data_router, prefix="/api/v1")
app.include_router(allowances_router, prefix="/api/v1")
app.include_router(deductions_router, prefix="/api/v1")
app.include_router(bonuses_router, prefix="/api/v1")
app.include_router(reimbursements_router, prefix="/api/v1")
app.include_router(kasbon_router, prefix="/api/v1")
app.include_router(thr_router, prefix="/api/v1")
app.include_router(company_entities_router, prefix="/api/v1")
app.include_router(rules_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    """Initialize database and seed data on startup."""
    init_db()
    db = SessionLocal()
    try:
        from app.seed.seed_data import seed_all
        seed_all(db)
    finally:
        db.close()


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint returning API info."""
    return {"message": "Indonesian Payroll & HRIS API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
