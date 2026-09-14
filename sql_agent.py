import torch
import duckdb

from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = r"C:\Users\moni2\Documents\models\Qwen2.5-3B-Instruct-bnb-4bit"

CSV_PATH = "data/kaggle_sales.csv"

DATABASE_PATH = "analytics.duckdb"

TABLE_NAME = "dataset"


# ============================================================
# LOAD QWEN
# ============================================================

print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH
)

print("Loading Qwen 3B...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    torch_dtype="auto"
)

model.eval()

print("Qwen loaded.")


# ============================================================
# DATABASE
# ============================================================

def get_database():

    con = duckdb.connect(DATABASE_PATH)

    con.execute(
        f"""
        CREATE OR REPLACE VIEW "{TABLE_NAME}" AS
        SELECT *
        FROM read_csv_auto('{CSV_PATH}')
        """
    )

    return con


# ============================================================
# GET DATABASE SCHEMA
# ============================================================

def get_schema():

    con = get_database()

    try:

        schema = con.execute(
            f'DESCRIBE "{TABLE_NAME}"'
        ).fetchall()

        return schema

    finally:

        con.close()


# ============================================================
# FORMAT SCHEMA
# ============================================================

def get_schema_text():

    schema = get_schema()

    schema_text = "\n".join(
        f"- {column[0]} ({column[1]})"
        for column in schema
    )

    return schema_text


# ============================================================
# SQL SAFETY
# ============================================================

def validate_sql(sql):

    if not sql:
        return False, "Empty SQL query."

    # --------------------------------------------------------
    # Remove Markdown code fences
    # --------------------------------------------------------

    sql_clean = sql.strip()

    sql_clean = sql_clean.replace(
        "```sql",
        ""
    )

    sql_clean = sql_clean.replace(
        "```SQL",
        ""
    )

    sql_clean = sql_clean.replace(
        "```",
        ""
    )

    sql_clean = sql_clean.strip()

    sql_lower = sql_clean.lower()

    # --------------------------------------------------------
    # Only SELECT / WITH
    # --------------------------------------------------------

    if not (
        sql_lower.startswith("select")
        or sql_lower.startswith("with")
    ):

        return False, (
            "Only SELECT or WITH queries are allowed."
        )

    # --------------------------------------------------------
    # Block dangerous SQL
    # --------------------------------------------------------

    forbidden = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "create ",
        "replace ",
        "grant ",
        "revoke ",
        "attach ",
        "detach ",
        "copy ",
        "install ",
        "load "
    ]

    for word in forbidden:

        if word in sql_lower:

            return False, (
                f"Forbidden SQL operation: "
                f"{word.strip()}"
            )

    # --------------------------------------------------------
    # Prevent multiple SQL statements
    # --------------------------------------------------------

    sql_without_trailing_semicolon = (
        sql_clean.rstrip(";").strip()
    )

    if ";" in sql_without_trailing_semicolon:

        return False, (
            "Multiple SQL statements are not allowed."
        )

    # --------------------------------------------------------
    # Make sure dataset table is used
    # --------------------------------------------------------

    if TABLE_NAME.lower() not in sql_lower:

        return False, (
            f"Query must use the '{TABLE_NAME}' table."
        )

    return True, sql_clean


# ============================================================
# GENERATE SQL
# ============================================================

def generate_sql(question):

    # --------------------------------------------------------
    # Automatically retrieve schema
    # --------------------------------------------------------

    schema_text = get_schema_text()

    # --------------------------------------------------------
    # QWEN SYSTEM PROMPT
    # --------------------------------------------------------

    system_prompt = f"""
You are a SQL Business Analytics Agent.

You generate DuckDB SQL queries.

The database contains one table:

{TABLE_NAME}

Available columns:

{schema_text}


IMPORTANT COLUMN RULE
=====================

Column names containing spaces, hyphens, or special
characters MUST be surrounded by double quotes.

Examples:

"Order ID"
"Sales Channel"
"ship-state"
"ship-city"
"Courier Status"

Normal column names may also be quoted.


SQL RULES
=========

1. Use ONLY the table `{TABLE_NAME}`.

2. Use ONLY columns from the provided schema.

3. Never invent a column.

4. Never invent a table.

5. Column names containing spaces or hyphens MUST
   be surrounded by double quotes.

6. Generate valid DuckDB SQL.

7. Only generate SELECT or WITH queries.

8. Never generate:

   INSERT
   UPDATE
   DELETE
   DROP
   ALTER
   CREATE
   TRUNCATE
   REPLACE
   GRANT
   REVOKE
   ATTACH
   DETACH
   COPY
   INSTALL
   LOAD

9. For totals, use SUM().

10. For averages, use AVG().

11. For counts, use COUNT().

12. For grouped analysis, use GROUP BY.

13. For rankings, use ORDER BY and LIMIT.

14. Use appropriate aliases for calculated columns.

15. Use WHERE for filtering.

16. Use ORDER BY for sorting.

17. Return ONLY SQL.

18. Do not explain the SQL.

19. Do not use Markdown.

20. Do not include ```sql.

21. Do not include any text before or after the SQL.


EXAMPLES
========

Question:
What is total sales?

SQL:
SELECT SUM("Amount") AS total_sales
FROM dataset;


Question:
Which state has the highest sales?

SQL:
SELECT
    "ship-state",
    SUM("Amount") AS total_sales
FROM dataset
GROUP BY "ship-state"
ORDER BY total_sales DESC
LIMIT 1;


Question:
What are the top 5 categories by sales?

SQL:
SELECT
    "Category",
    SUM("Amount") AS total_sales
FROM dataset
GROUP BY "Category"
ORDER BY total_sales DESC
LIMIT 5;


Question:
How many orders are there?

SQL:
SELECT COUNT(*) AS total_orders
FROM dataset;
"""

    # --------------------------------------------------------
    # CHAT MESSAGES
    # --------------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # --------------------------------------------------------
    # CREATE CHAT PROMPT
    # --------------------------------------------------------

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # --------------------------------------------------------
    # TOKENIZE
    # --------------------------------------------------------

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    )

    # --------------------------------------------------------
    # MOVE TO MODEL DEVICE
    # --------------------------------------------------------

    inputs = {
        key: value.to(model.device)
        for key, value in inputs.items()
    }

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_new_tokens=250,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    # --------------------------------------------------------
    # REMOVE INPUT TOKENS
    # --------------------------------------------------------

    generated_tokens = outputs[
        0
    ][
        inputs["input_ids"].shape[-1]:
    ]

    # --------------------------------------------------------
    # DECODE
    # --------------------------------------------------------

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    # --------------------------------------------------------
    # VALIDATE GENERATED SQL
    # --------------------------------------------------------

    valid, checked_sql = validate_sql(
        response
    )

    if not valid:

        raise ValueError(
            f"SQL validation failed: {checked_sql}"
        )

    return checked_sql


# ============================================================
# EXECUTE SQL
# ============================================================

def execute_sql(sql):

    con = get_database()

    try:

        result = con.execute(
            sql
        ).fetchall()

        columns = [
            description[0]
            for description in con.description
        ]

        return columns, result

    finally:

        con.close()


# ============================================================
# RUN AGENT WITH AUTOMATIC RETRY
# ============================================================

def run_agent(question):

    print("\nGenerating SQL...\n")

    # --------------------------------------------------------
    # Generate initial SQL
    # --------------------------------------------------------

    sql = generate_sql(question)

    # --------------------------------------------------------
    # Maximum 3 attempts
    # --------------------------------------------------------

    for attempt in range(3):

        print(
            f"\nAttempt {attempt + 1}"
        )

        print(
            "--------------------------------"
        )

        print(sql)

        print(
            "--------------------------------"
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        valid, checked_sql = validate_sql(
            sql
        )

        if not valid:

            print(
                "\nSQL validation failed:"
            )

            print(
                checked_sql
            )

            sql = generate_sql(
                f"""
User question:

{question}

Your previous SQL was invalid.

Reason:

{checked_sql}

Generate a corrected DuckDB SELECT query.

Use ONLY the provided database schema.

Return ONLY SQL.
"""
            )

            continue

        # ----------------------------------------------------
        # EXECUTE
        # ----------------------------------------------------

        try:

            columns, results = execute_sql(
                checked_sql
            )

            # Successful query
            return (
                checked_sql,
                columns,
                results
            )

        except Exception as error:

            print(
                "\nSQL execution error:"
            )

            print(error)

            # ------------------------------------------------
            # Get schema again
            # ------------------------------------------------

            schema_text = get_schema_text()

            # ------------------------------------------------
            # Correction prompt
            # ------------------------------------------------

            correction_prompt = f"""
The SQL query below failed to execute.

USER QUESTION
=============

{question}


DATABASE
========

Table:

{TABLE_NAME}


AVAILABLE COLUMNS
=================

{schema_text}


FAILED SQL
==========

{checked_sql}


DATABASE ERROR
==============

{error}


TASK
====

Generate a corrected DuckDB SQL query.


RULES
=====

1. Use ONLY the `{TABLE_NAME}` table.

2. Use ONLY columns from the provided schema.

3. Never invent columns.

4. Never invent tables.

5. Columns containing spaces or hyphens MUST
   use double quotes.

6. Generate valid DuckDB SQL.

7. Only generate SELECT or WITH queries.

8. Do not use INSERT.

9. Do not use UPDATE.

10. Do not use DELETE.

11. Do not use DROP.

12. Do not use ALTER.

13. Do not use CREATE.

14. Do not use TRUNCATE.

15. Do not use REPLACE.

16. Do not use GRANT.

17. Do not use REVOKE.

18. Return ONLY SQL.

19. Do not use Markdown.

20. Do not explain anything.
"""

            try:

                sql = generate_sql(
                    correction_prompt
                )

            except Exception as generation_error:

                print(
                    "\nCorrection generation error:"
                )

                print(
                    generation_error
                )

                continue

    # --------------------------------------------------------
    # ALL RETRIES FAILED
    # --------------------------------------------------------

    raise RuntimeError(
        "Could not generate a valid SQL query "
        "after 3 attempts."
    )


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(
    columns,
    results
):

    print("\nColumns:")

    print(
        columns
    )

    print("\nResults:")

    if not results:

        print(
            "No results found."
        )

        return

    for row in results:

        print(row)


# ============================================================
# DISPLAY DATABASE SCHEMA
# ============================================================

def display_schema():

    print(
        "\nDATABASE SCHEMA"
    )

    print(
        "--------------------------------"
    )

    schema = get_schema()

    for column in schema:

        print(
            f"{column[0]:35} {column[1]}"
        )

    print(
        "--------------------------------"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        "      SQL BUSINESS ANALYTICS AGENT"
    )

    print(
        "========================================"
    )

    print(
        f"\nDatabase : {DATABASE_PATH}"
    )

    print(
        f"CSV      : {CSV_PATH}"
    )

    print(
        f"Table    : {TABLE_NAME}"
    )

    # --------------------------------------------------------
    # Test database and schema
    # --------------------------------------------------------

    try:

        display_schema()

    except Exception as error:

        print(
            "\nDATABASE ERROR:"
        )

        print(error)

        raise SystemExit(1)

    print(
        "\nAgent ready."
    )

    # --------------------------------------------------------
    # INTERACTIVE LOOP
    # --------------------------------------------------------

    while True:

        question = input(
            "\nAsk a business question "
            "(type 'exit' to quit): "
        )

        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if question.lower().strip() in [
            "exit",
            "quit",
            "q"
        ]:

            print(
                "\nGoodbye!"
            )

            break

        # ----------------------------------------------------
        # EMPTY QUESTION
        # ----------------------------------------------------

        if not question.strip():

            print(
                "Please enter a question."
            )

            continue

        # ----------------------------------------------------
        # RUN AGENT
        # ----------------------------------------------------

        try:

            sql, columns, results = run_agent(
                question
            )

            # ------------------------------------------------
            # FINAL SQL
            # ------------------------------------------------

            print(
                "\nFINAL SQL:"
            )

            print(
                "--------------------------------"
            )

            print(sql)

            print(
                "--------------------------------"
            )

            # ------------------------------------------------
            # RESULTS
            # ------------------------------------------------

            display_results(
                columns,
                results
            )

        except Exception as error:

            print(
                "\nAGENT ERROR:"
            )

            print(error)