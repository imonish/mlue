import duckdb

con = duckdb.connect("analytics.duckdb")

print("\n==============================")
print("KAGGLE DATASET TEST")
print("==============================")

# Total amount
result = con.execute("""
    SELECT SUM(Amount)
    FROM dataset
""").fetchone()

print("\nTotal Amount:")
print(result[0])


# Total quantity
result = con.execute("""
    SELECT SUM(Qty)
    FROM dataset
""").fetchone()

print("\nTotal Quantity:")
print(result[0])


# Orders by state
result = con.execute("""
    SELECT
        "ship-state",
        COUNT(*) AS orders
    FROM dataset
    GROUP BY "ship-state"
    ORDER BY orders DESC
    LIMIT 10
""").fetchall()

print("\nTop 10 States:")
for row in result:
    print(row)


# Sales by category
result = con.execute("""
    SELECT
        Category,
        SUM(Amount) AS revenue
    FROM dataset
    GROUP BY Category
    ORDER BY revenue DESC
""").fetchall()

print("\nRevenue by Category:")
for row in result:
    print(row)


con.close()