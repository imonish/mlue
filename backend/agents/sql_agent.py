
import re
import pandas as pd

from backend.models.omnisql_model import OmniSQLModel
from backend.database.database import DatabaseManager
from backend.tools.sql_validator import validate_sql


class SQLAgent:

    def __init__(self, database_path="data/analytics.duckdb"):
        print("Initializing MLUE SQL Agent...")

        # Load model once
        self.model = OmniSQLModel()

        # Connect to DuckDB
        self.db = DatabaseManager(database_path)

        print("SQL Agent initialized successfully!")

    def get_schema_text(self):
        """Convert database schema into a prompt-friendly format."""

        schema = self.db.get_schema("dataset")

        columns = []

        for column in schema:
            columns.append(
                f"{column['column']} ({column['type']})"
            )

        return "Table: dataset\nColumns:\n" + "\n".join(columns)

    def build_prompt(self, question, error=None, previous_sql=None):
        """Build the SQL generation prompt."""

        schema = self.get_schema_text()

        prompt = f"""
You are an expert DuckDB SQL query generator.

Your task is to generate a correct SQL query for the user's question.

DATABASE SCHEMA:
{schema}

RULES:
- Use only the table and columns listed in the schema.
- Generate DuckDB-compatible SQL.
- Only generate SELECT queries.
- Do not modify the database.
- Return only the SQL query.
- Do not include explanations or Markdown.

USER QUESTION:
{question}

SQL:
"""

        if error:
            prompt += f"""

The previous SQL query failed.

Previous SQL:
{previous_sql}

Error:
{error}

Generate a corrected SQL query.
SQL:
"""

        return prompt

    def extract_sql(self, response):
        """Extract SQL from model output."""

        # Remove Markdown SQL code fences
        match = re.search(
            r"```sql\s*(.*?)```",
            response,
            re.IGNORECASE | re.DOTALL,
        )

        if match:
            response = match.group(1)

        else:
            response = re.sub(
                r"```",
                "",
                response,
            )

        # Extract the first SELECT or WITH statement
        match = re.search(
            r"\b(SELECT|WITH)\b.*",
            response,
            re.IGNORECASE | re.DOTALL,
        )

        if not match:
            raise ValueError(
                "The model did not generate a SQL query."
            )

        sql = match.group(0).strip()

        # Remove trailing semicolon
        sql = sql.rstrip(";").strip()

        return sql

    def run(self, question, max_retries=2):
        """Generate, validate, execute and retry SQL."""

        print(f"\nQuestion: {question}")

        previous_sql = None
        last_error = None

        for attempt in range(max_retries + 1):

            print(
                f"\nSQL generation attempt "
                f"{attempt + 1}/{max_retries + 1}"
            )

            prompt = self.build_prompt(
                question=question,
                error=last_error,
                previous_sql=previous_sql,
            )

            response = self.model.generate(
                prompt,
                max_new_tokens=256,
            )

            print("\nModel response:")
            print(response)

            try:
                sql = self.extract_sql(response)

                print("\nGenerated SQL:")
                print(sql)

                # Validate before execution
                sql = validate_sql(sql)

                # Execute query
                result = self.db.execute_query(sql)

                print("\nQuery executed successfully!")

                return {
                    "success": True,
                    "question": question,
                    "sql": sql,
                    "columns": list(result.columns),
                    "rows": result.to_dict(
                        orient="records"
                    ),
                    "row_count": len(result),
                    "attempts": attempt + 1,
                }

            except Exception as error:

                last_error = str(error)
                previous_sql = (
                    sql if "sql" in locals()
                    else response
                )

                print("\nSQL execution failed:")
                print(last_error)

                if attempt < max_retries:
                    print("Retrying...")

        return {
            "success": False,
            "question": question,
            "sql": previous_sql,
            "error": last_error,
            "attempts": max_retries + 1,
        }

    def close(self):
        self.db.close()
