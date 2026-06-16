from __future__ import annotations

import hashlib


def fingerprint(*fields: str | None) -> str:
    h = hashlib.sha1()
    for f in fields:
        h.update((f or "").strip().lower().encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


def job_fingerprint(title: str | None, company: str | None, city: str | None) -> str:
    return fingerprint(title, company, city)
