SQL_QA_TEMPLATE = f"""Addtionally, follow these instructions:

        ALWAYS include the name of the documents in your query results by joining with the `doc_info` table using the `doc_id` foreign key. This ensures that the results clearly indicate which document each row originates from.

        If the user's question involves aggregations, counts, or summaries, ensure that the `doc_info.doc_name` column is included in the `GROUP BY` clause and appears alongside the aggregated values in the results. For example, if counting rows, include `doc_info.doc_name` in the result.

        Always verify your SQL query includes the name of the relevant documents in the result set before execution. If it doesn't, modify the query to include it.

        ### Response Format Example
        Your final response must be in the following JSON format:

        ```json
        {{
        "input": "<User's original question>",
        "output": [
            {{
            "doc_name": "<Name of the document>",
            "<relevant_field_1>": "<value>",
            "<relevant_field_2>": "<value>",
            ...
            }},
            ...
        ]
        }}
        ```

        For example, if the input is: "Check if there are any instances of people signing more than 3 times."
        Your response should look like this:

        ```json
        {{
            "input": "Check if there are any instances of people signing more than 3 times.",
            "output": [
                {{
                "doc_name": "Document A",
                "signer_name": "Head - QA",
                "signature_count": 4
                }},
                {{
                "doc_name": "Document B",
                "signer_name": "Supervisor",
                "signature_count": 5
                }}
            ]
        }}
        ```
        This ensures that:
        
        ALWAYS validate that your output adheres to this format before returning it to the user. If the query cannot return any results, indicate this explicitly in the output field as an empty array.
        """

import sqlite3
from typing import Any, Dict, Optional


def connect_to_db(db_path: str) -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    print(f"Connected to database at {db_path}")
    return conn


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """
    Check if a table exists in the SQLite database.
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table_name,),
    )
    return cursor.fetchone() is not None


def get_sql_type(value: Any) -> str:
    """
    Map a Python value to a SQLite column type.
    """
    if isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "REAL"
    elif isinstance(value, str) or value is None:
        return "TEXT"
    else:
        raise ValueError(f"Unsupported JSON value type: {type(value)}")


def ensure_column_exists(
    cursor: sqlite3.Cursor, table_name: str, column_name: str, column_type: str
) -> None:
    """
    Ensure a column exists in a table. If not, add it dynamically.
    """
    cursor.execute(f"PRAGMA table_info({table_name});")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if column_name not in existing_columns:
        try:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};"
            )
            print(
                f"[SCHEMA] Added column '{column_name}' ({column_type}) to table '{table_name}'."
            )
        except sqlite3.OperationalError as e:
            print(
                f"[ERROR] Failed to add column '{column_name}' to table '{table_name}': {e}"
            )


def insert_data(
    cursor: sqlite3.Cursor,
    table_name: str,
    data: Dict[str, Any],
    doc_id: int,
    ensure_column_fn: callable,
) -> Optional[int]:
    """
    Insert data into the table. For nested structures, insert into sub-tables.
    Dynamically adds missing columns.
    """
    columns = ["doc_id"]
    values = [doc_id]

    for key, value in data.items():
        if isinstance(value, dict):
            sub_table = f"{table_name}_{key}"
            nested_id = insert_data(cursor, sub_table, value, doc_id, ensure_column_fn)
            columns.append(f"{key}_id")
            values.append(nested_id)
            ensure_column_fn(cursor, table_name, f"{key}_id", "INTEGER")
        elif isinstance(value, list):
            sub_table = f"{table_name}_{key}"
            for item in value:
                if isinstance(item, dict):
                    insert_data(cursor, sub_table, item, doc_id, ensure_column_fn)
        else:
            col_type = get_sql_type(value)
            columns.append(key)
            values.append(value)
            ensure_column_fn(cursor, table_name, key, col_type)

    if len(columns) > 1:
        placeholders = ", ".join(["?"] * len(values))
        insert_sql = f"""
        INSERT INTO {table_name} ({", ".join(columns)})
        VALUES ({placeholders});
        """
        try:
            cursor.execute(insert_sql, values)
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Insert IntegrityError in {table_name}: {e}")
        except sqlite3.OperationalError as e:
            print(f"[ERROR] Insert into {table_name} failed: {e}")
    return None


def get_sql_type(value: Any) -> str:
    """
    Map a Python value to a SQLite column type.
    """
    if isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "REAL"
    elif isinstance(value, str):
        return "TEXT"
    elif value is None:
        return "TEXT"
    else:
        raise ValueError(f"Unsupported JSON value type: {type(value)}")
