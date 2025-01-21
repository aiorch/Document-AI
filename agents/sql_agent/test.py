import sqlite3

DB_PATH = "./batch_data.db"  # Update this if your database path is different


def inspect_database(db_path):
    """
    Inspect the database and print all tables, their schema, and a preview of their data.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        print("No tables found in the database.")
        conn.close()
        return

    print(f"\nTables in the database '{db_path}':\n")
    for table in tables:
        table_name = table[0]
        print(f"Table: {table_name}")

        # Fetch schema for the table
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema = cursor.fetchall()
        print("Schema:")
        for col in schema:
            print(f"  - {col[1]} ({col[2]})")

        # Fetch first 5 rows of data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
        rows = cursor.fetchall()
        if rows:
            print("Data (first 5 rows):")
            for row in rows:
                print(f"  {row}")
        else:
            print("  No data found in this table.")

        print("-" * 40)

    conn.close()


if __name__ == "__main__":
    inspect_database(DB_PATH)
