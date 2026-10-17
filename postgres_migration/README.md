# PostgreSQL migration module

This folder is intentionally isolated from the existing project files so that the current implementation remains untouched.

## Purpose

Add a PostgreSQL-ready database layer for the existing skin analysis service without editing the original app files.

## Environment variables

Set these before connecting:

- POSTGRES_HOST
- POSTGRES_PORT
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_SSLMODE

## Quick start

1. Install PostgreSQL client support:

```bash
pip install psycopg2-binary
```

2. Create a database named `mirrorme` (or set POSTGRES_DB to another name).

3. Run the migration:

```bash
python -m postgres_migration.migration --sqlite-db skincare.db --host localhost --port 5432 --dbname mirrorme --user postgres --password postgres
```

## What it does

- Creates the `users` table if missing
- Creates the `skin_analyses` table if missing
- Copies rows from the existing SQLite database into PostgreSQL
- Keeps the original project code untouched

## Notes

This module is intended as a separate production migration route, not a replacement for the working local SQLite app.
