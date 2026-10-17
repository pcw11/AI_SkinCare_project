import json
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

try:
    import psycopg2
except Exception:  # pragma: no cover
    psycopg2 = None

from .config import PostgresConfig


def get_connection(config: Optional[PostgresConfig] = None):
    if psycopg2 is None:
        raise RuntimeError(
            "psycopg2 is not installed. Install it with: pip install psycopg2-binary"
        )

    cfg = config or PostgresConfig.from_env()
    return psycopg2.connect(cfg.dsn)


def ensure_tables(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email VARCHAR UNIQUE,
                password_hash VARCHAR,
                nickname VARCHAR,
                gender VARCHAR,
                birth_year INTEGER,
                skin_type VARCHAR,
                skin_concern TEXT,
                allergy_ingredients TEXT,
                preferred_formulations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS skin_analyses (
                analyses_id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                image_url VARCHAR,
                score_total INTEGER,
                score_acne INTEGER,
                score_pore INTEGER,
                score_pigmentation INTEGER,
                score_sebum INTEGER,
                raw_values JSONB,
                bbox_coordinates TEXT,
                llm_report JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.commit()


def _fetch_sqlite_rows(sqlite_db_path: str | Path) -> Tuple[list, list]:
    path = Path(sqlite_db_path)
    if not path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {path}")

    conn = sqlite3.connect(str(path))
    users = conn.execute(
        "SELECT user_id, email, password_hash, nickname, gender, birth_year, skin_type, skin_concern, allergy_ingredients, preferred_formulations, created_at FROM users"
    ).fetchall()
    analyses = conn.execute(
        "SELECT user_id, image_url, score_total, score_acne, score_pore, score_pigmentation, score_sebum, raw_values, bbox_coordinates, llm_report, created_at FROM skin_analyses"
    ).fetchall()
    conn.close()
    return users, analyses


def _normalize_pg_json(value):
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    if isinstance(value, str):
        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            return value
    return value


def migrate_sqlite_to_postgres(sqlite_db_path: str | Path, config: Optional[PostgresConfig] = None) -> dict:
    cfg = config or PostgresConfig.from_env()
    conn = get_connection(cfg)
    ensure_tables(conn)

    users, analyses = _fetch_sqlite_rows(sqlite_db_path)

    with conn.cursor() as cur:
        if users:
            cur.executemany(
                """
                INSERT INTO users (
                    user_id, email, password_hash, nickname, gender, birth_year,
                    skin_type, skin_concern, allergy_ingredients, preferred_formulations, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                [
                    (
                        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]
                    )
                    for row in users
                ],
            )

        if analyses:
            cur.executemany(
                """
                INSERT INTO skin_analyses (
                    user_id, image_url, score_total, score_acne, score_pore,
                    score_pigmentation, score_sebum, raw_values, bbox_coordinates, llm_report, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s)
                ON CONFLICT DO NOTHING
                """,
                [
                    (
                        row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                        _normalize_pg_json(row[7]),
                        row[8],
                        _normalize_pg_json(row[9]),
                        row[10],
                    )
                    for row in analyses
                ],
            )

    conn.commit()
    conn.close()

    return {
        "users": len(users),
        "analyses": len(analyses),
        "target": cfg.dsn,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate SQLite data into PostgreSQL")
    parser.add_argument("--sqlite-db", default="skincare.db", help="Path to the SQLite database")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="5432")
    parser.add_argument("--dbname", default="mirrorme")
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--password", default="postgres")
    args = parser.parse_args()

    config = PostgresConfig(
        host=args.host,
        port=int(args.port),
        dbname=args.dbname,
        user=args.user,
        password=args.password,
    )
    print(migrate_sqlite_to_postgres(args.sqlite_db, config))
