import pytest

from app.metrics import compute_growth_from_net_income, compute_growth_over_pe, compute_growth_rate


def test_compute_growth_rate_uses_assignment_formula():
    result = compute_growth_rate(100.0, 125.0)
    assert result == 25.0


def test_compute_growth_from_net_income_latest_two_years():
    reports = [
        {"fiscalDateEnding": "2025-12-31", "netIncome": "140"},
        {"fiscalDateEnding": "2024-12-31", "netIncome": "100"},
    ]
    assert round(compute_growth_from_net_income(reports), 2) == 40.0


def test_compute_growth_over_pe():
    assert compute_growth_over_pe(20.0, 10.0) == 2.0


def test_growth_over_pe_requires_positive_pe():
    with pytest.raises(ValueError):
        compute_growth_over_pe(20.0, 0)
