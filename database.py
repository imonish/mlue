import duckdb

CSV_PATH = "data/sales.csv"

def get_connection():
    return duckdb.connect("analytics.duckdb")


def setup_database():
    con = get_connection()

    con.execute(f"""
        CREATE OR REPLACE VIEW sales AS
        SELECT *
        FROM read_csv_auto('{CSV_PATH}')
    """)

    return con


def get_schema():
    con = setup_database()

    result = con.execute("""
        DESCRIBE sales
    """).fetchall()

    con.close()

    return result


def get_sample_rows():
    con = setup_database()

    result = con.execute("""
        SELECT *
        FROM sales
        LIMIT 5
    """).fetchall()

    con.close()

    return result


if __name__ == "__main__":
    print("\n=== SCHEMA ===")

    for row in get_schema():
        print(row)

    print("\n=== SAMPLE DATA ===")

    for row in get_sample_rows():
        print(row)