"""Isolated PostgreSQL migration utilities for the skin analysis service.

This package is intentionally separate from the existing app files so that
other developers' code remains untouched while a production-ready PostgreSQL
migration path can be validated independently.
"""

from .config import PostgresConfig
from .migration import ensure_tables, get_connection, migrate_sqlite_to_postgres

__all__ = [
    "PostgresConfig",
    "ensure_tables",
    "get_connection",
    "migrate_sqlite_to_postgres",
]
