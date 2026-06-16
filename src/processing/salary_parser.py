from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_NEGOTIABLE_TOKENS = ("面議", "negotiable", "依公司規定", "依面議", "面試議定")
_HOURLY_TOKENS = ("時薪", "hourly", "per hour", "/hr")
_ANNUAL_TOKENS = ("年薪", "annual", "per year", "/year", "yearly")
_MONTHLY_TOKENS = ("月薪", "monthly", "/month")

_NUMBER_PATTERN = re.compile(
    r"(?P<value>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(?P<unit>k|K|萬|m|M|百萬)?"
)
_RANGE_SEPARATOR = re.compile(r"\s*(?:~|-|–|—|to|至|\bto\b)\s*", re.IGNORECASE)


@dataclass
class SalaryRange:
    min_monthly_twd: Optional[int]
    max_monthly_twd: Optional[int]
    confidence: float
    period_detected: str  # "monthly" | "annual" | "hourly" | "unknown"


def _scale(value: float, unit: Optional[str]) -> float:
    if not unit:
        return value
    unit = unit.lower()
    if unit == "k":
        return value * 1_000
    if unit == "萬":
        return value * 10_000
    if unit in ("m", "百萬"):
        return value * 1_000_000
    return value


def _detect_period(text: str) -> str:
    low = text.lower()
    if any(t in text or t in low for t in _MONTHLY_TOKENS):
        return "monthly"
    if any(t in text or t in low for t in _ANNUAL_TOKENS):
        return "annual"
    if any(t in text or t in low for t in _HOURLY_TOKENS):
        return "hourly"
    return "unknown"


def _to_monthly(amount: float, period: str) -> float:
    if period == "annual":
        return amount / 12.0
    if period == "hourly":
        return amount * 22 * 8
    return amount


def _extract_numbers(text: str) -> list[float]:
    found: list[float] = []
    for m in _NUMBER_PATTERN.finditer(text):
        raw = m.group("value").replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        found.append(_scale(value, m.group("unit")))
    return found


def parse_salary_text(text: Optional[str]) -> SalaryRange:
    if not text:
        return SalaryRange(None, None, 0.0, "unknown")

    if any(tok in text.lower() or tok in text for tok in _NEGOTIABLE_TOKENS):
        return SalaryRange(None, None, 0.0, "unknown")

    period = _detect_period(text)
    parts = _RANGE_SEPARATOR.split(text, maxsplit=1)
    lo: Optional[float] = None
    hi: Optional[float] = None

    if len(parts) == 2:
        lo_nums = _extract_numbers(parts[0])
        hi_nums = _extract_numbers(parts[1])
        if lo_nums and hi_nums:
            lo, hi = lo_nums[-1], hi_nums[0]
    if lo is None or hi is None:
        nums = _extract_numbers(text)
        if len(nums) == 0:
            return SalaryRange(None, None, 0.0, period)
        if len(nums) == 1:
            lo = hi = nums[0]
        else:
            lo, hi = nums[0], nums[1]

    if period == "unknown":
        anchor = max(lo, hi)
        if anchor >= 500_000:
            period = "annual"
        elif anchor < 1_000:
            period = "hourly"
        else:
            period = "monthly"

    lo_monthly = _to_monthly(lo, period)
    hi_monthly = _to_monthly(hi, period)
    if lo_monthly > hi_monthly:
        lo_monthly, hi_monthly = hi_monthly, lo_monthly

    confidence = 0.9 if period in ("monthly", "annual") else 0.4
    if lo_monthly == hi_monthly:
        confidence *= 0.6

    return SalaryRange(
        min_monthly_twd=int(round(lo_monthly)),
        max_monthly_twd=int(round(hi_monthly)),
        confidence=round(confidence, 2),
        period_detected=period,
    )
