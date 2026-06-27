"""Shared fixtures for payroll calculation engine tests."""
import pytest
from decimal import Decimal

from app.calculations.pph21_pasal17 import TaxBracket
from app.calculations.pph21_ter import TerBracketData
from app.calculations.bpjs import BpjsConfig


@pytest.fixture
def pasal17_brackets():
    """UU HPP 2022 (UU 7/2021) progressive tax brackets for Pasal 17.

    - 0 - 60,000,000: 5%
    - >60,000,000 - 250,000,000: 15%
    - >250,000,000 - 500,000,000: 25%
    - >500,000,000 - 5,000,000,000: 30%
    - >5,000,000,000: 35%
    """
    return [
        TaxBracket(
            lower_bound=Decimal("0"),
            upper_bound=Decimal("60000000"),
            rate=Decimal("0.05"),
        ),
        TaxBracket(
            lower_bound=Decimal("60000000"),
            upper_bound=Decimal("250000000"),
            rate=Decimal("0.15"),
        ),
        TaxBracket(
            lower_bound=Decimal("250000000"),
            upper_bound=Decimal("500000000"),
            rate=Decimal("0.25"),
        ),
        TaxBracket(
            lower_bound=Decimal("500000000"),
            upper_bound=Decimal("5000000000"),
            rate=Decimal("0.30"),
        ),
        TaxBracket(
            lower_bound=Decimal("5000000000"),
            upper_bound=Decimal("999999999999"),
            rate=Decimal("0.35"),
        ),
    ]


@pytest.fixture
def sample_ter_brackets():
    """Sample TER brackets for Category A, B, and C per PMK 168/2023.

    Simplified brackets for testing. Real data has many more ranges.
    """
    return [
        # Category A brackets
        TerBracketData(
            category="A",
            income_range_min=Decimal("0"),
            income_range_max=Decimal("5400000"),
            ter_rate=Decimal("0"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("5400001"),
            income_range_max=Decimal("5650000"),
            ter_rate=Decimal("0.0025"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("5650001"),
            income_range_max=Decimal("5950000"),
            ter_rate=Decimal("0.005"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("5950001"),
            income_range_max=Decimal("6300000"),
            ter_rate=Decimal("0.0075"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("6300001"),
            income_range_max=Decimal("6750000"),
            ter_rate=Decimal("0.01"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("6750001"),
            income_range_max=Decimal("7500000"),
            ter_rate=Decimal("0.0125"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("7500001"),
            income_range_max=Decimal("8550000"),
            ter_rate=Decimal("0.015"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("8550001"),
            income_range_max=Decimal("9650000"),
            ter_rate=Decimal("0.0175"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("9650001"),
            income_range_max=Decimal("10050000"),
            ter_rate=Decimal("0.02"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("10050001"),
            income_range_max=Decimal("10350000"),
            ter_rate=Decimal("0.0225"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("10350001"),
            income_range_max=Decimal("10700000"),
            ter_rate=Decimal("0.025"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("10700001"),
            income_range_max=Decimal("11050000"),
            ter_rate=Decimal("0.03"),
        ),
        TerBracketData(
            category="A",
            income_range_min=Decimal("11050001"),
            income_range_max=Decimal("11600000"),
            ter_rate=Decimal("0.035"),
        ),
        # Category B brackets
        TerBracketData(
            category="B",
            income_range_min=Decimal("0"),
            income_range_max=Decimal("6200000"),
            ter_rate=Decimal("0"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("6200001"),
            income_range_max=Decimal("6500000"),
            ter_rate=Decimal("0.0025"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("6500001"),
            income_range_max=Decimal("6850000"),
            ter_rate=Decimal("0.005"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("6850001"),
            income_range_max=Decimal("7300000"),
            ter_rate=Decimal("0.0075"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("7300001"),
            income_range_max=Decimal("9200000"),
            ter_rate=Decimal("0.01"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("9200001"),
            income_range_max=Decimal("10750000"),
            ter_rate=Decimal("0.015"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("10750001"),
            income_range_max=Decimal("11250000"),
            ter_rate=Decimal("0.02"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("11250001"),
            income_range_max=Decimal("11600000"),
            ter_rate=Decimal("0.025"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("11600001"),
            income_range_max=Decimal("12500000"),
            ter_rate=Decimal("0.03"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("12500001"),
            income_range_max=Decimal("13750000"),
            ter_rate=Decimal("0.035"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("13750001"),
            income_range_max=Decimal("15100000"),
            ter_rate=Decimal("0.04"),
        ),
        TerBracketData(
            category="B",
            income_range_min=Decimal("15100001"),
            income_range_max=Decimal("16950000"),
            ter_rate=Decimal("0.05"),
        ),
        # Category C brackets
        TerBracketData(
            category="C",
            income_range_min=Decimal("0"),
            income_range_max=Decimal("6600000"),
            ter_rate=Decimal("0"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("6600001"),
            income_range_max=Decimal("6950000"),
            ter_rate=Decimal("0.0025"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("6950001"),
            income_range_max=Decimal("7350000"),
            ter_rate=Decimal("0.005"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("7350001"),
            income_range_max=Decimal("7800000"),
            ter_rate=Decimal("0.0075"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("7800001"),
            income_range_max=Decimal("8850000"),
            ter_rate=Decimal("0.01"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("8850001"),
            income_range_max=Decimal("9800000"),
            ter_rate=Decimal("0.015"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("9800001"),
            income_range_max=Decimal("10950000"),
            ter_rate=Decimal("0.02"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("10950001"),
            income_range_max=Decimal("11200000"),
            ter_rate=Decimal("0.025"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("11200001"),
            income_range_max=Decimal("12050000"),
            ter_rate=Decimal("0.03"),
        ),
        TerBracketData(
            category="C",
            income_range_min=Decimal("12050001"),
            income_range_max=Decimal("12950000"),
            ter_rate=Decimal("0.035"),
        ),
    ]


@pytest.fixture
def sample_bpjs_settings():
    """Standard BPJS settings with typical Indonesian rates and caps.

    - KESEHATAN: 5% (4% employer, 1% employee), cap 12,000,000
    - JHT: 5.7% (3.7% employer, 2% employee), no cap
    - JP: 3% (2% employer, 1% employee), cap 9,559,600
    - JKK: 0.24% employer only, no cap
    - JKM: 0.3% employer only, no cap
    """
    return {
        "KESEHATAN": BpjsConfig(
            bpjs_type="KESEHATAN",
            employee_rate=Decimal("0.01"),
            employer_rate=Decimal("0.04"),
            max_salary_base=Decimal("12000000"),
        ),
        "JHT": BpjsConfig(
            bpjs_type="JHT",
            employee_rate=Decimal("0.02"),
            employer_rate=Decimal("0.037"),
            max_salary_base=None,
        ),
        "JP": BpjsConfig(
            bpjs_type="JP",
            employee_rate=Decimal("0.01"),
            employer_rate=Decimal("0.02"),
            max_salary_base=Decimal("9559600"),
        ),
        "JKK": BpjsConfig(
            bpjs_type="JKK",
            employee_rate=Decimal("0"),
            employer_rate=Decimal("0.0024"),
            max_salary_base=None,
        ),
        "JKM": BpjsConfig(
            bpjs_type="JKM",
            employee_rate=Decimal("0"),
            employer_rate=Decimal("0.003"),
            max_salary_base=None,
        ),
    }


@pytest.fixture
def ptkp_tk0():
    """PTKP for TK/0 (single, no dependents) = 54,000,000/year."""
    return Decimal("54000000")


@pytest.fixture
def ptkp_k1():
    """PTKP for K/1 (married, 1 dependent) = 63,000,000/year."""
    return Decimal("63000000")


@pytest.fixture
def sample_employee():
    """Sample employee data for integration-style tests."""
    return {
        "name": "John Doe",
        "ptkp_status": "TK/0",
        "ptkp_annual": Decimal("54000000"),
        "base_salary": Decimal("10000000"),
        "work_week_type": "5_DAY",
    }
