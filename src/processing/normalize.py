from __future__ import annotations

import re

_TITLE_RULES: list[tuple[re.Pattern, tuple[str, str]]] = [
    (re.compile(r"(?i)(senior|sr\.?|staff|資深).*(backend|後端).*(engineer|工程師|developer|開發)"),
        ("Senior Backend Engineer", "Engineering")),
    (re.compile(r"(?i)(senior|sr\.?|staff|資深).*(frontend|前端).*(engineer|工程師|developer|開發)"),
        ("Senior Frontend Engineer", "Engineering")),
    (re.compile(r"(?i)(senior|sr\.?|staff|資深).*(data|資料|數據).*(engineer|工程師)"),
        ("Senior Data Engineer", "Data")),
    (re.compile(r"(?i)(research[- ]?scientist|research engineer|研究員)"),
        ("Research Engineer", "ML")),
    (re.compile(r"(?i)(backend|後端).*(engineer|工程師|developer|開發)"),
        ("Backend Engineer", "Engineering")),
    (re.compile(r"(?i)(frontend|前端).*(engineer|工程師|developer|開發)"),
        ("Frontend Engineer", "Engineering")),
    (re.compile(r"(?i)(full[ -]?stack|全端).*(engineer|工程師|developer)"),
        ("Full-Stack Engineer", "Engineering")),
    (re.compile(r"(?i)(mobile|iOS|Android).*(engineer|工程師|developer)"),
        ("Mobile Engineer", "Engineering")),
    (re.compile(r"(?i)(data|資料|數據).*(engineer|工程師)"),
        ("Data Engineer", "Data")),
    (re.compile(r"(?i)(data|資料|數據).*(scientist|科學家)"),
        ("Data Scientist", "Data")),
    (re.compile(r"(?i)(ml|machine[- ]learning|機器學習|deep[- ]learning|ai).*(engineer|工程師)"),
        ("ML Engineer", "ML")),
    (re.compile(r"(?i)(devops|site reliability|sre|平台工程)"),
        ("DevOps/SRE", "Infra")),
    (re.compile(r"(?i)(security|資安).*(engineer|工程師)"),
        ("Security Engineer", "Infra")),
    (re.compile(r"(?i)(product manager|產品經理|\bpm\b)"),
        ("Product Manager", "Product")),
    (re.compile(r"(?i)(qa|test|品保|測試).*(engineer|工程師)"),
        ("QA Engineer", "Engineering")),
    (re.compile(r"(?i)(software|軟體).*(engineer|工程師)"),
        ("Software Engineer", "Engineering")),
]

_COMPANY_ALIASES = {
    "tsmc": "TSMC",
    "台積電": "TSMC",
    "mediatek": "MediaTek",
    "聯發科": "MediaTek",
    "google taiwan": "Google",
    "google 台灣": "Google",
    "google": "Google",
    "amazon web services": "AWS",
    "appier": "Appier",
    "趨勢科技": "Trend Micro",
    "trend micro": "Trend Micro",
    "微軟": "Microsoft",
    "microsoft": "Microsoft",
    "iKala": "iKala",
    "kkbox": "KKBOX",
    "shopback": "ShopBack",
    "shopline": "SHOPLINE",
    "91app": "91APP",
    "玉山金控": "E.SUN",
    "cathay": "Cathay",
    "國泰": "Cathay",
    "line": "LINE",
    "line taiwan": "LINE",
}

# Order matters: a more-specific city must come before any city whose
# keyword is a substring of it (e.g. "New Taipei" before "Taipei").
_CITY_KEYWORDS = {
    "New Taipei": ["新北", "new taipei"],
    "Taipei":     ["台北", "臺北", "taipei"],
    "Hsinchu":    ["新竹", "hsinchu"],
    "Taoyuan":    ["桃園", "taoyuan"],
    "Taichung":   ["台中", "臺中", "taichung"],
    "Tainan":     ["台南", "臺南", "tainan"],
    "Kaohsiung":  ["高雄", "kaohsiung"],
    "Remote":     ["remote", "遠端"],
}

_YOE_RANGE = re.compile(r"(\d{1,2})\s*(?:~|-|–|至|to)\s*(\d{1,2})\s*(?:年|yrs?|years?)", re.IGNORECASE)
_YOE_SINGLE = re.compile(r"(\d{1,2})\s*\+?\s*(?:年|yrs?|years?)(?:\s*(?:以上|plus))?", re.IGNORECASE)


def normalize_title(raw: str | None) -> tuple[str, str]:
    if not raw:
        return ("Unclassified", "Other")
    for pattern, label in _TITLE_RULES:
        if pattern.search(raw):
            return label
    return ("Unclassified", "Other")


def normalize_company(raw: str | None) -> str:
    if not raw:
        return "Unknown"
    key = raw.strip().lower()
    if key in _COMPANY_ALIASES:
        return _COMPANY_ALIASES[key]
    for alias, canonical in _COMPANY_ALIASES.items():
        if alias in key:
            return canonical
    return raw.strip()


def extract_city(location: str | None) -> str:
    if not location:
        return "Unknown"
    low = location.lower()
    for city, keywords in _CITY_KEYWORDS.items():
        if any(k in location or k in low for k in keywords):
            return city
    return "Other"


def extract_yoe(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return (None, None)
    m = _YOE_RANGE.search(text)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = _YOE_SINGLE.search(text)
    if m:
        v = int(m.group(1))
        return (v, v + 5)
    return (None, None)
