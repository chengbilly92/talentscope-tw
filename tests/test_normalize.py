from src.processing.normalize import (
    extract_city,
    extract_yoe,
    normalize_company,
    normalize_title,
)


def test_senior_title_is_preserved():
    title, family = normalize_title("Senior Backend Engineer")
    assert title == "Senior Backend Engineer"
    assert family == "Engineering"


def test_basic_title():
    title, family = normalize_title("Backend Engineer")
    assert title == "Backend Engineer"
    assert family == "Engineering"


def test_data_engineer_chinese():
    title, family = normalize_title("資料工程師")
    assert title == "Data Engineer"
    assert family == "Data"


def test_company_alias():
    assert normalize_company("台積電") == "TSMC"
    assert normalize_company("Google Taiwan") == "Google"


def test_city_from_chinese_address():
    assert extract_city("台北市信義區") == "Taipei"
    assert extract_city("Hsinchu, Taiwan") == "Hsinchu"


def test_new_taipei_is_not_collapsed_to_taipei():
    """Regression: 'New Taipei市' must not match the 'taipei' substring rule
    before the 'new taipei' rule. This used to bucket all New Taipei
    postings into Taipei, hiding the second-largest TW tech-employment
    city from any per-city query."""
    assert extract_city("New Taipei市") == "New Taipei"
    assert extract_city("新北市板橋區") == "New Taipei"


def test_yoe_single_value():
    lo, hi = extract_yoe("Required: 5+ years of experience")
    assert lo == 5
    assert hi is not None and hi > lo
