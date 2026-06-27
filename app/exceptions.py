class PayrollError(Exception):
    """Base exception for all payroll errors."""

    def __init__(self, message: str, detail: dict = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(self.message)


class TaxCalculationError(PayrollError):
    """Raised when tax calculation fails."""
    pass


class BpjsCalculationError(PayrollError):
    """Raised when BPJS calculation fails."""
    pass


class OvertimeCalculationError(PayrollError):
    """Raised when overtime calculation fails."""
    pass


class PayrollValidationError(PayrollError):
    """Raised when business rule validation fails."""
    pass


class InsufficientConfigError(PayrollError):
    """Raised when required configuration is missing or inactive."""
    pass


class PayrollRunError(PayrollError):
    """Raised when payroll run processing fails."""
    pass


class DuplicatePayrollRunError(PayrollError):
    """Raised when a duplicate payroll run is detected."""
    pass
