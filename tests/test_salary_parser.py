from src.processing.salary_parser import parse_salary_text


def test_chinese_monthly_range():
    s = parse_salary_text("月薪 50,000 ~ 80,000 元")
    assert s.min_monthly_twd == 50_000
    assert s.max_monthly_twd == 80_000
    assert s.period_detected == "monthly"
    assert s.confidence >= 0.8


def test_chinese_annual_range_converts_to_monthly():
    s = parse_salary_text("年薪 1,200,000 ~ 1,800,000 元")
    assert s.min_monthly_twd == 100_000
    assert s.max_monthly_twd == 150_000
    assert s.period_detected == "annual"


def test_k_notation():
    s = parse_salary_text("60K ~ 90K (月薪)")
    assert s.min_monthly_twd == 60_000
    assert s.max_monthly_twd == 90_000


def test_wan_notation():
    s = parse_salary_text("月薪 5萬 ~ 8萬")
    assert s.min_monthly_twd == 50_000
    assert s.max_monthly_twd == 80_000


def test_negotiable_returns_none():
    s = parse_salary_text("面議")
    assert s.min_monthly_twd is None
    assert s.max_monthly_twd is None


def test_english_monthly():
    s = parse_salary_text("Monthly NT$70,000 - NT$110,000")
    assert s.min_monthly_twd == 70_000
    assert s.max_monthly_twd == 110_000


def test_empty_input():
    s = parse_salary_text("")
    assert s.min_monthly_twd is None
    assert s.confidence == 0.0


def test_single_number_no_range():
    s = parse_salary_text("月薪 65,000 元")
    assert s.min_monthly_twd == 65_000
    assert s.max_monthly_twd == 65_000


def test_period_inference_when_unstated():
    s = parse_salary_text("1,500,000 ~ 2,000,000")
    assert s.period_detected == "annual"
    assert 100_000 <= s.min_monthly_twd <= 200_000
