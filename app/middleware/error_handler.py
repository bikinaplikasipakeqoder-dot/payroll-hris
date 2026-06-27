"""
Global exception handler middleware.
Maps custom PayrollError exceptions to appropriate HTTP responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    PayrollError,
    TaxCalculationError,
    BpjsCalculationError,
    OvertimeCalculationError,
    PayrollValidationError,
    InsufficientConfigError,
    PayrollRunError,
    DuplicatePayrollRunError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app instance."""

    @app.exception_handler(PayrollValidationError)
    async def payroll_validation_error_handler(request: Request, exc: PayrollValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "PayrollValidationError",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(DuplicatePayrollRunError)
    async def duplicate_payroll_run_error_handler(request: Request, exc: DuplicatePayrollRunError):
        return JSONResponse(
            status_code=409,
            content={
                "error": "DuplicatePayrollRunError",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(InsufficientConfigError)
    async def insufficient_config_error_handler(request: Request, exc: InsufficientConfigError):
        return JSONResponse(
            status_code=424,
            content={
                "error": "InsufficientConfigError",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(TaxCalculationError)
    async def tax_calculation_error_handler(request: Request, exc: TaxCalculationError):
        return JSONResponse(
            status_code=500,
            content={
                "error": "TaxCalculationError",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(BpjsCalculationError)
    async def bpjs_calculation_error_handler(request: Request, exc: BpjsCalculationError):
        return JSONResponse(
            status_code=500,
            content={
                "error": "BpjsCalculationError",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(OvertimeCalculationError)
    async def overtime_calculation_error_handler(request: Request, exc: OvertimeCalculationError):
        return JSONResponse(
            status_code=500,
            content={
                "error": "OvertimeCalculationError",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(PayrollRunError)
    async def payroll_run_error_handler(request: Request, exc: PayrollRunError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "PayrollRunError",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(PayrollError)
    async def payroll_error_handler(request: Request, exc: PayrollError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "PayrollError",
                "message": exc.message,
                "detail": exc.detail,
            },
        )
