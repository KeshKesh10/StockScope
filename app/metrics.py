from typing import Any


def to_float(value: Any) -> float:
    if value in (None, "", "None", "-"):
        raise ValueError("Value is missing")
    return float(value)


def compute_growth_rate(beginning_value: float, ending_value: float) -> float:
    if beginning_value == 0:
        raise ValueError("Beginning value cannot be zero")
    return ((ending_value - beginning_value) / beginning_value) * 100


def compute_growth_from_net_income(reports: list[dict[str, Any]]) -> float:
    if len(reports) < 2:
        raise ValueError("At least two annual reports are required")

    sorted_reports = sorted(
        reports, key=lambda report: report.get("fiscalDateEnding", ""), reverse=True
    )
    ending_value = to_float(sorted_reports[0].get("netIncome"))
    beginning_value = to_float(sorted_reports[1].get("netIncome"))
    return compute_growth_rate(beginning_value, ending_value)


def compute_growth_over_pe(growth_rate: float, pe_ratio: float) -> float:
    if pe_ratio <= 0:
        raise ValueError("P/E ratio must be positive")
    return growth_rate / pe_ratio
