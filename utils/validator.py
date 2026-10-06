def validate_sql(sql: str):

    blocked = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "CREATE"
    ]

    upper_sql = sql.upper()

    for command in blocked:
        if command in upper_sql:
            return False

    return True