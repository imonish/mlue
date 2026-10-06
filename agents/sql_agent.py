import torch
import duckdb

from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = r"C:\Users\moni2\Documents\mlue\Qwen2.5-3B-Instruct-bnb-4bit"

CSV_PATH = r"C:\Users\moni2\Documents\mlue\data\kaggle_sales.csv"

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
# VALUE LOOKUP
# ============================================================

def get_distinct_values(column_name, limit=100):

    conn = get_database()

    try:

        query = f'''
            SELECT DISTINCT "{column_name}"
            FROM "{TABLE_NAME}"
            WHERE "{column_name}" IS NOT NULL
            LIMIT {limit}
        '''

        result = conn.execute(query).fetchall()

        return [row[0] for row in result]

    finally:

        conn.close()


def find_matching_value(column_name, user_value):

    conn = get_database()

    try:

        query = f'''
            SELECT DISTINCT "{column_name}"
            FROM "{TABLE_NAME}"
            WHERE LOWER(CAST("{column_name}" AS VARCHAR))
                  = LOWER(?)
            LIMIT 1
        '''

        result = conn.execute(
            query,
            [user_value]
        ).fetchone()

        return result[0] if result else None

    finally:

        conn.close()


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

IMPORTANT:

You are NOT an answer-generating assistant.

Your ONLY job is to generate executable DuckDB SQL.

NEVER explain the dataset.
NEVER describe columns in natural language.
NEVER answer the user's question directly.
NEVER output Markdown.
NEVER output explanations.
NEVER output headings.

Your response MUST contain ONLY one SQL query.

The query MUST start with SELECT or WITH.

If the user asks "Describe the dataset", do NOT write a textual description.

Generate SQL that can retrieve useful dataset statistics instead.


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

1. Use ONLY the table "{TABLE_NAME}".

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


User: What is total sales?

Output:

SELECT SUM("Amount") AS total_sales
FROM dataset;


User: Which state has the highest sales?

Output:

SELECT
    "ship-state",
    SUM("Amount") AS total_sales
FROM dataset
GROUP BY "ship-state"
ORDER BY total_sales DESC
LIMIT 1;


User: What are the top 5 categories by sales?

Output:

SELECT
    "Category",
    SUM("Amount") AS total_sales
FROM dataset
GROUP BY "Category"
ORDER BY total_sales DESC
LIMIT 5;


User: How many orders are there?

Output:

SELECT COUNT(*) AS total_orders
FROM dataset;


User: Describe the dataset

Output:

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT "Order ID") AS unique_orders,
    COUNT(DISTINCT "Category") AS unique_categories,
    COUNT(DISTINCT "ship-state") AS unique_states,
    MIN("Date") AS earliest_date,
    MAX("Date") AS latest_date,
    SUM("Amount") AS total_sales
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

    generated_tokens = outputs[0][
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
    # DEBUG: SHOW RAW QWEN RESPONSE
    # --------------------------------------------------------

    print("\nRAW QWEN RESPONSE:")
    print("--------------------------------")
    print(response)
    print("--------------------------------")

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
# RUN AGENT
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

1. Use ONLY the "{TABLE_NAME}" table.

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
# LANGGRAPH SQL AGENT NODE
# ============================================================

def run_sql_agent(state):

    # --------------------------------------------------------
    # Get question from LangGraph state
    # --------------------------------------------------------

    question = state["user_query"]

    print("\n========================================")
    print("          LANGGRAPH SQL AGENT")
    print("========================================")

    print(
        f"\nUser Question: {question}"
    )

    # --------------------------------------------------------
    # Get schema
    # --------------------------------------------------------

    print(
        "\nGetting database schema..."
    )

    schema_text = get_schema_text()

    # --------------------------------------------------------
    # Generate initial SQL
    # --------------------------------------------------------

    print(
        "\nQwen is generating SQL..."
    )

    sql = generate_sql(question)

    # --------------------------------------------------------
    # Maximum 3 attempts
    # --------------------------------------------------------

    for attempt in range(3):

        print(
            f"\nSQL Attempt {attempt + 1}/3"
        )

        print(
            "--------------------------------"
        )

        print(sql)

        print(
            "--------------------------------"
        )

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        valid, checked_sql = validate_sql(
            sql
        )

        if not valid:

            print(
                "\nValidation failed:"
            )

            print(
                checked_sql
            )

            # ------------------------------------------------
            # Ask Qwen to fix the SQL
            # ------------------------------------------------

            correction_question = f"""
User question:

{question}

Previous SQL:

{sql}

Validation error:

{checked_sql}

Generate a corrected DuckDB SELECT query.

Use ONLY the provided database schema.

Return ONLY SQL.
"""

            try:

                sql = generate_sql(
                    correction_question
                )

                continue

            except Exception as error:

                print(
                    "\nCorrection generation failed:"
                )

                print(error)

                continue

        # ----------------------------------------------------
        # Execute SQL
        # ----------------------------------------------------

        try:

            columns, results = execute_sql(
                checked_sql
            )

            print(
                "\nSQL executed successfully."
            )

            print(
                f"Rows returned: {len(results)}"
            )

            # ------------------------------------------------
            # Return LangGraph state
            # ------------------------------------------------

            return {

                "user_query": question,

                "generated_sql": checked_sql,

                "sql_result": results,

                "sql_columns": columns,

                "schema": schema_text,

                "error": None
            }

        except Exception as error:

            print(
                "\nSQL execution error:"
            )

            print(error)

            # ------------------------------------------------
            # Ask Qwen to correct SQL
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

1. Use ONLY the "{TABLE_NAME}" table.

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

    return {

        "user_query": question,

        "generated_sql": sql,

        "sql_result": [],

        "sql_columns": [],

        "schema": schema_text,

        "error": (
            "Could not generate and execute "
            "valid SQL after 3 attempts."
        )
    }


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
# NORMAL SQL AGENT TEST
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

    # --------------------------------------------------------
    # TEST VALUE LOOKUP
    # --------------------------------------------------------

    print(
        "\nTesting distinct values for ship-state..."
    )

    try:

        values = get_distinct_values(
            "ship-state"
        )

        print(values)

    except Exception as error:

        print(
            "\nVALUE LOOKUP ERROR:"
        )

        print(error)

    print(
        "\nTesting case-insensitive value lookup..."
    )

    try:

        result = find_matching_value(
            "ship-state",
            "Maharashtra"
        )

        print(
            f"Maharashtra -> {result}"
        )

    except Exception as error:

        print(
            "\nMATCHING VALUE ERROR:"
        )

        print(error)

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
        # RUN NORMAL AGENT
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