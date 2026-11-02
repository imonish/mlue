
import re


BLOCKED_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "COPY",
    "ATTACH",
    "DETACH",
    "EXPORT",
    "IMPORT",
    "INSTALL",
    "LOAD",
    "CALL",
    "SET",
    "RESET",
}


def validate_sql(sql: str) -> str:
    """Validate generated SQL before execution."""

    if not sql or not sql.strip():
        raise ValueError("SQL query is empty")

    # Remove Markdown code fences
    sql = re.sub(r"```(?:sql)?", "", sql, flags=re.IGNORECASE)
    sql = sql.strip()

    # Permit one optional trailing semicolon
    sql = sql.rstrip(";").strip()

    if ";" in sql:
        raise ValueError("Only one SQL statement is allowed")

    # Require a read-only query
    if not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise ValueError("Only SELECT or WITH queries are allowed")

    # Block destructive and administrative statements
    for keyword in BLOCKED_KEYWORDS:
        pattern = rf"\b{keyword}\b"

        if re.search(pattern, sql, re.IGNORECASE):
            raise ValueError(
                f"Blocked SQL keyword: {keyword}"
            )

    return sql
