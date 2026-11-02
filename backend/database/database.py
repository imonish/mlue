
import duckdb
from pathlib import Path


class DatabaseManager:

    def __init__(self, database_path="data/analytics.duckdb"):
        path = Path(database_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = duckdb.connect(str(path))

        print(f"DuckDB connected: {path.resolve()}")

    def get_schema(self, table_name="dataset"):
        result = self.connection.execute(
            f"DESCRIBE {table_name}"
        ).fetchall()

        return [
            {"column": row[0], "type": row[1]}
            for row in result
        ]

    def execute_query(self, sql: str):
        return self.connection.execute(sql).fetchdf()

    def close(self):
        self.connection.close()
