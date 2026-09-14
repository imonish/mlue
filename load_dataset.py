import duckdb
import sys
import os


if len(sys.argv) < 2:
    print("Usage:")
    print("python load_dataset.py data/your_file.csv")
    sys.exit(1)


csv_path = sys.argv[1]

if not os.path.exists(csv_path):
    print(f"File not found: {csv_path}")
    sys.exit(1)


con = duckdb.connect("analytics.duckdb")


con.execute(f"""
    CREATE OR REPLACE VIEW dataset AS
    SELECT *
    FROM read_csv_auto('{csv_path}')
""")


print("\n==============================")
print("DATASET LOADED")
print("==============================")

print(f"File: {csv_path}")


print("\nSCHEMA")
print("------------------------------")

schema = con.execute(
    "DESCRIBE dataset"
).fetchall()

for column in schema:
    print(
        f"{column[0]:30} {column[1]}"
    )


print("\nSAMPLE DATA")
print("------------------------------")

rows = con.execute("""
    SELECT *
    FROM dataset
    LIMIT 5
""").fetchall()

for row in rows:
    print(row)


print("\nROW COUNT")
print("------------------------------")

count = con.execute("""
    SELECT COUNT(*)
    FROM dataset
""").fetchone()[0]

print(count)


con.close()