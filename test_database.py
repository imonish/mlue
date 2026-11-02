
from backend.database.database import DatabaseManager
from backend.database.dataset_loader import load_csv
from backend.tools.sql_validator import validate_sql


print("=" * 50)
print("MLUE - DATABASE TEST")
print("=" * 50)

db = DatabaseManager()

# Load the dataset
info = load_csv(
    "data/datasets/sales.csv",
    db.connection,
    "dataset",
)

print("\nDataset loaded:")
print(info)

# Inspect schema
print("\nSchema:")
print(db.get_schema())

# Execute a test query
sql = """
SELECT
    product,
    SUM(quantity * price) AS revenue
FROM dataset
GROUP BY product
ORDER BY revenue DESC
LIMIT 5
"""

print("\nValidating SQL...")
sql = validate_sql(sql)

print("SQL is valid!")

print("\nExecuting query...")
result = db.execute_query(sql)

print(result)

db.close()

print("\nDatabase test completed!")
