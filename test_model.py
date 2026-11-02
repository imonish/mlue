
from backend.models.omnisql_model import OmniSQLModel

print("=" * 50)
print("MLUE - OmniSQL-7B MODEL TEST")
print("=" * 50)

model = OmniSQLModel()

prompt = """
You are a SQL generation assistant.
Generate a DuckDB SQL query for the following request.

Table: sales
Columns: product, quantity, price

Question: Find the top 5 products by total revenue.

SQL:
"""

print("\nGenerating SQL...")

response = model.generate(
    prompt,
    max_new_tokens=128,
)

print("\nGenerated SQL:")
print(response)

print("\nModel test completed!")
