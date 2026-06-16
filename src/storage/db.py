from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb

from src.config import DB_PATH

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=read_only)


@contextmanager
def session(read_only: bool = False) -> Iterator[duckdb.DuckDBPyConnection]:
    conn = connect(read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()


def init_schema() -> None:
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    with session() as conn:
        conn.execute(sql)
