
from pathlib import Path
import duckdb
import pandas as pd
import re


def validate_table_name(name: str) -> str:
    """Allow only safe SQL identifiers."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError("Invalid table name")
    return name


def load_csv(
    csv_path: str,
    connection: duckdb.DuckDBPyConnection,
    table_name: str = "dataset",
) -> dict:
    """Load a CSV into DuckDB and return its schema."""

    path = Path(csv_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    table_name = validate_table_name(table_name)

    # Read CSV using Pandas for reliable type inference
    df = pd.read_csv(path)

    if df.empty:
        raise ValueError("The CSV contains no rows")

    if len(df.columns) == 0:
        raise ValueError("The CSV contains no columns")

    # Register the dataframe temporarily with DuckDB
    connection.register("_uploaded_dataframe", df)

    try:
        connection.execute(
            f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM _uploaded_dataframe
            """
        )
    finally:
        connection.unregister("_uploaded_dataframe")

    schema_rows = connection.execute(
        f"DESCRIBE {table_name}"
    ).fetchall()

    schema = [
        {
            "column": row[0],
            "type": row[1],
            "nullable": row[2],
        }
        for row in schema_rows
    ]

    row_count = connection.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    return {
        "table_name": table_name,
        "row_count": row_count,
        "column_count": len(schema),
        "columns": schema,
    }
