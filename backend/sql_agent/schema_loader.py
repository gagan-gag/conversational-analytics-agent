"""
sql_agent/schema_loader.py — SQLAlchemy schema introspection.

Generates a human-readable schema string injected into the SQL agent's
system prompt so the LLM knows exactly what tables and columns exist.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from sqlalchemy import create_engine, inspect, text

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Human-readable type mapping ──────────────────────────────────────────────
_TYPE_MAP = {
    "INTEGER": "INTEGER",
    "REAL": "REAL (float)",
    "TEXT": "TEXT",
    "DATE": "DATE (YYYY-MM-DD)",
    "DATETIME": "DATETIME (YYYY-MM-DD HH:MM:SS)",
    "BLOB": "BLOB",
    "NUMERIC": "NUMERIC",
}


@lru_cache(maxsize=1)
def get_schema_string() -> str:
    """
    Introspect the SQLite DB and return a human-readable schema description.
    Cached after first call — call invalidate_schema_cache() if schema changes.
    """
    engine = create_engine(f"sqlite:///{settings.sqlite_db_path}", echo=False)
    inspector = inspect(engine)

    lines = ["# Analytics Database Schema\n"]
    lines.append("Database: SQLite (read-only)\n")
    lines.append("=" * 60 + "\n")

    table_names = inspector.get_table_names()
    if not table_names:
        return "No tables found in database."

    for table in table_names:
        lines.append(f"\n## Table: `{table}`")

        # Columns
        columns = inspector.get_columns(table)
        lines.append("\n| Column | Type | Nullable | Default |")
        lines.append("|--------|------|----------|---------|")
        for col in columns:
            col_type = str(col["type"]).upper()
            nullable = "YES" if col.get("nullable", True) else "NO"
            default = str(col.get("default", "—")) or "—"
            lines.append(f"| `{col['name']}` | {col_type} | {nullable} | {default} |")

        # Primary keys
        pk = inspector.get_pk_constraint(table)
        if pk and pk.get("constrained_columns"):
            lines.append(f"\n**Primary Key:** {', '.join(pk['constrained_columns'])}")

        # Foreign keys
        fks = inspector.get_foreign_keys(table)
        if fks:
            for fk in fks:
                lines.append(
                    f"**Foreign Key:** `{', '.join(fk['constrained_columns'])}` → "
                    f"`{fk['referred_table']}.{', '.join(fk['referred_columns'])}`"
                )

        # Row count + sample values for categorical columns
        try:
            with engine.connect() as conn:
                row_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                lines.append(f"\n**Row Count:** ~{row_count:,}")

                # Show distinct values for short-cardinality TEXT columns
                for col in columns:
                    if str(col["type"]).upper() == "TEXT":
                        distinct = conn.execute(
                            text(f"SELECT DISTINCT `{col['name']}` FROM `{table}` LIMIT 10")
                        ).fetchall()
                        vals = [str(r[0]) for r in distinct if r[0] is not None]
                        if 1 < len(vals) <= 10:
                            lines.append(
                                f"  - `{col['name']}` sample values: {', '.join(vals)}"
                            )
        except Exception as e:
            logger.warning("Could not fetch sample data for table %s: %s", table, e)

    schema = "\n".join(lines)
    logger.info("Schema loaded: %d tables", len(table_names))
    return schema


def invalidate_schema_cache() -> None:
    get_schema_string.cache_clear()
