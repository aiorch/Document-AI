import json
import os
from typing import Any, Dict

from dotenv import load_dotenv

from agents.sql_agent.utils import (
    connect_to_db,
    ensure_column_exists,
    get_sql_type,
    insert_data,
    table_exists,
)

script_dir = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(script_dir, ".env")
load_dotenv(ENV_PATH)

DB_PATH = "/Users/siyengar/Desktop/dev/Document-AI/agents/sql_agent/batch_data_json.db"
KNOWLEDGE_BASE_DIR = os.path.join(script_dir, "../knowledge_base")


class JSONToSQL:
    def __init__(self, db_path: str):
        self.conn = connect_to_db(db_path)
        self.cursor = self.conn.cursor()
        self.table_schemas = {}
        self.create_doc_info_table()

    def create_doc_info_table(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS doc_info (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_name TEXT UNIQUE
            )
            """
        )
        self.conn.commit()

    def resolve_doc_id(self, doc_name: str) -> int:
        self.cursor.execute(
            "INSERT OR IGNORE INTO doc_info (doc_name) VALUES (?);", (doc_name,)
        )
        self.conn.commit()
        self.cursor.execute(
            "SELECT doc_id FROM doc_info WHERE doc_name = ?;", (doc_name,)
        )
        row = self.cursor.fetchone()
        if not row:
            raise RuntimeError(f"Failed to resolve doc_id for {doc_name}")
        return row[0]

    def gather_schema(self, table_name: str, data: Dict[str, Any]) -> None:
        if table_name not in self.table_schemas:
            self.table_schemas[table_name] = set()
            self.table_schemas[table_name].add("pk INTEGER PRIMARY KEY AUTOINCREMENT")
            self.table_schemas[table_name].add("doc_id INTEGER")

        for key, value in data.items():
            if isinstance(value, dict):
                sub_table = f"{table_name}_{key}"
                self.gather_schema(sub_table, value)
                self.table_schemas[table_name].add(f"{key}_id INTEGER")
            elif isinstance(value, list):
                sub_table = f"{table_name}_{key}"
                for item in value:
                    if isinstance(item, dict):
                        self.gather_schema(sub_table, item)
            else:
                col_type = get_sql_type(value)
                col_def = f"{key} {col_type}"
                self.table_schemas[table_name].add(col_def)

    def create_tables_from_schema(self) -> None:
        for table_name, columns in self.table_schemas.items():
            if table_exists(self.cursor, table_name):
                continue
            fk_constraint = "FOREIGN KEY (doc_id) REFERENCES doc_info(doc_id)"
            col_list = sorted(list(columns))
            create_sql = f"""
            CREATE TABLE {table_name} (
                {", ".join(col_list)},
                {fk_constraint}
            );
            """
            self.cursor.execute(create_sql)
            print(f"[SCHEMA] Created table {table_name} with {len(col_list)} columns.")

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    loader = JSONToSQL(DB_PATH)

    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
            print(f"\n[PROCESSING] {filename}")

            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            doc_id = loader.resolve_doc_id(filename)
            loader.gather_schema("main_table", json_data)
            loader.create_tables_from_schema()
            insert_data(
                loader.cursor, "main_table", json_data, doc_id, ensure_column_exists
            )

    loader.commit()
    loader.close()
