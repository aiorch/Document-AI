import importlib.util
import json
import os
import sqlite3
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError
from pydantic.errors import PydanticUserError

SCHEMA_DIR = "schemas"
SQL_SCRIPTS_DIR = "sql_scripts"
KNOWLEDGE_BASE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../knowledge_base"
)

script_dir = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(script_dir, ".env")
load_dotenv(ENV_PATH)

DB_PATH = os.getenv("SQL_DB_PATH", os.path.join(script_dir, "batch_data.db"))
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-instruct")


class DynamicSQLLoader:
    """
    Dynamically manages SQL tables and data insertion for different document types.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        print(f"Connected to database at: {self.db_path}")

    def close(self):
        self.conn.close()
        print("Database connection closed.")

    def clear_database(self):
        """
        Drop all existing tables in the database.
        """
        self.cursor.execute(
            "PRAGMA foreign_keys = OFF;"
        )  # Disable foreign key checks temporarily
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = self.cursor.fetchall()
        for table_name in tables:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]};")
        self.cursor.execute("PRAGMA foreign_keys = ON;")  # Re-enable foreign key checks
        print("Database cleared.")

    def create_doc_info_table(self):
        """
        Create the `doc_info` table for mapping document names to unique IDs.
        """
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
        """
        Insert or retrieve the doc_id for a given doc_name in `doc_info`.

        Args:
            doc_name (str): The document name.

        Returns:
            int: The corresponding doc_id.
        """
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO doc_info (doc_name) VALUES (?)
            """,
            (doc_name,),
        )
        self.conn.commit()
        self.cursor.execute(
            """
            SELECT doc_id FROM doc_info WHERE doc_name = ?
            """,
            (doc_name,),
        )
        row = self.cursor.fetchone()
        if row:
            return row[0]
        raise RuntimeError(f"Failed to resolve doc_id for {doc_name}")

    def identify_schema(self, json_data: dict) -> Optional[str]:
        """
        Identify the schema type for the given JSON data by validating it
        against all available schemas in the `schemas` folder.

        Args:
            json_data (dict): JSON data to match with a schema.

        Returns:
            Optional[str]: The name of the schema file (without .py) if matched, else None.
        """
        for schema_file in os.listdir(SCHEMA_DIR):
            if not schema_file.endswith(".py"):
                continue
            schema_path = os.path.join(SCHEMA_DIR, schema_file)
            module_name = f"schemas.{schema_file[:-3]}"
            spec = importlib.util.spec_from_file_location(module_name, schema_path)
            schema_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(schema_module)

            # Match JSON data against the schema
            for attr_name in dir(schema_module):
                attr = getattr(schema_module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseModel):
                    try:
                        attr.parse_obj(json_data)  # Try to parse JSON
                        return "inspection_form"
                    except Exception or ValidationError or PydanticUserError:
                        continue
        return None

    def ensure_sql_script(self, schema_name: str, schema_code: str):
        """
        Ensures a Python script exists for the given schema.
        If not, generates it dynamically using GPT.

        Args:
            schema_name (str): The name of the schema.
            schema_code (str): The Pydantic schema code.
        """
        script_path = os.path.join(SQL_SCRIPTS_DIR, f"{schema_name}.py")
        if not os.path.exists(script_path):
            print(f"No SQL script found for '{schema_name}'. Generating...")
            script_code = self._generate_script_with_llm(schema_name, schema_code)
            self._save_script(script_path, script_code)
        else:
            print(f"SQL script for '{schema_name}' already exists.")

    def execute_sql_script(
        self,
        schema_name: str,
        action: str,
        json_data: Optional[dict] = None,
        doc_id: Optional[int] = None,
    ):
        """
        Execute the `create_tables` or `insert_data` function from the SQL script.

        Args:
            schema_name (str): The name of the schema.
            action (str): Either 'create_tables' or 'insert_data'.
            json_data (Optional[dict]): Data to insert when action is 'insert_data'.
            doc_id (Optional[int]): The doc_id to include in insert_data.

        Returns:
            bool: Whether the action succeeded.
        """
        script_path = os.path.join(SQL_SCRIPTS_DIR, f"{schema_name}.py")
        module_name = f"sql_scripts.{schema_name}"
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        sql_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sql_module)

        func = getattr(sql_module, action, None)
        if not func:
            raise ValueError(
                f"Function '{action}' not found in script for '{schema_name}'."
            )

        if action == "create_tables":
            success = func(self.cursor)
        elif action == "insert_data" and json_data and doc_id is not None:
            success = func(self.cursor, json_data, doc_id)
        else:
            raise ValueError(f"Invalid action '{action}' or missing parameters.")

        self.conn.commit()
        return success

    def _generate_script_with_llm(self, schema_name: str, schema_code: str) -> str:
        """
        Generate a Python SQL script using GPT.

        Args:
            schema_name (str): The name of the schema.
            schema_code (str): The Pydantic schema code.

        Returns:
            str: The generated Python script.
        """
        prompt = f"""
        You are provided with a Pydantic schema named '{schema_name}': {schema_code}

        Write a Python script with only the following two functions:

        1. `create_tables(cursor)`:
            - This function creates SQLite tables for the schema **plus** a table named `doc_info(doc_id INTEGER PRIMARY KEY AUTOINCREMENT, doc_name TEXT UNIQUE)`.
            - Every table in the schema must include a `doc_id INTEGER` column referencing `doc_info(doc_id)` to associate rows with their respective document.
            - Use `id INTEGER PRIMARY KEY AUTOINCREMENT` for the table rows if needed.
            - Use foreign keys where relationships are implied by the schema.
            - Ensure all column names and data types match the schema accurately. For example:
                - Text fields should be defined as `TEXT`.
                - Numerical fields as `INTEGER` or `REAL`, based on the schema.
            - Ensure that tables contain all the fields provided in the schema, including optional fields where applicable.
            - Do not leave any table incomplete. If a schema field maps to a table, its corresponding column **must** be included.
            - Make sure to handle nested schemas in the table definitions.
            - Validate that there are no duplicate columns in any table definitions.
            - Return a boolean value indicating whether the function succeeded.
            - DO NOT INCLUDE DUPLICATE COLUMNS IN THE DEFINITION OF THE TABLE.

        2. `insert_data(cursor, json_data, doc_id)`:
            - This function inserts JSON data (validated by the schema) into the SQLite tables created above.
            - Use `doc_id` to fill the `doc_id` column in every insert statement, ensuring each row is tagged with the correct document.
            - For every `INSERT` statement:
                - Use `INSERT OR IGNORE` only for the primary parent table if avoiding duplicates.
                - Use regular `INSERT` for all child tables.
                - Ensure the number of columns in the `INSERT` statement matches the number of values in the `VALUES` clause.
                - Handle missing or optional fields gracefully using `.get()` to provide `None` for missing keys.
            - Wrap each `INSERT` statement in a `try-except` block to handle and log errors gracefully:
            ```python
            try:
                cursor.execute("INSERT INTO table_name (...) VALUES (...)", (...))
            except sqlite3.IntegrityError as e:
                # Log the error and continue
                print(f"Failed to insert data into table_name: {{e}}")
            ```
            - Ensure that if the parent table row already exists, its primary key is retrieved and used for child inserts.
            - Use parameterized SQL queries for inserting data to prevent SQL injection.
            - Return a boolean value indicating whether the function succeeded.

        ### Example:

        ```python
        def create_tables(cursor):
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS doc_info (
                    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_name TEXT UNIQUE
                )
                '''
            )

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS material_usage_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id INTEGER,
                    raw_material TEXT,
                    unit TEXT,
                    standard_quantity REAL,
                    allowed_range_min REAL,
                    allowed_range_max REAL,
                    actual_quantity REAL,
                    in_house_batch_no TEXT,
                    performed_by TEXT,
                    checked_by TEXT,
                    remarks TEXT,
                    FOREIGN KEY (doc_id) REFERENCES doc_info(doc_id)
                )
                '''
            )

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS manufacturing_procedure (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id INTEGER,
                    op_no INTEGER,
                    description TEXT,
                    equipment_no TEXT,
                    date TEXT,
                    time_from TEXT,
                    time_to TEXT,
                    duration TEXT,
                    performed_by TEXT,
                    checked_by TEXT,
                    remarks TEXT,
                    FOREIGN KEY (doc_id) REFERENCES doc_info(doc_id)
                )
                '''
            )

        def insert_data(cursor, json_data, doc_id):
            try:
                if "manufacturing_procedure" in json_data:
                    for step in json_data["manufacturing_procedure"]["steps"]:
                        equipment_no = step.get("equipment_no")
                        if isinstance(equipment_no, list):
                            equipment_no = ','.join(map(str, equipment_no))
                        cursor.execute(
                            '''
                            INSERT INTO manufacturing_procedure (doc_id, op_no, description, equipment_no, date, time_from, time_to, duration, performed_by, checked_by, remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''',
                            (
                                doc_id,
                                step.get("op_no"),
                                step.get("description"),
                                equipment_no,
                                step.get("date"),
                                step.get("time_from"),
                                step.get("time_to"),
                                step.get("duration"),
                                step.get("performed_by"),
                                step.get("checked_by"),
                                step.get("remarks")
                            )
                        )
            except Exception as e:
                print(f"Failed to insert into batch_details: {{e}}")

            try:
                if "material_usage_table" in json_data:
                    for row in json_data["material_usage_table"]["rows"]:
                        cursor.execute(
                            '''
                            INSERT INTO material_usage_row (doc_id, raw_material, unit, standard_quantity, allowed_range_min, allowed_range_max, actual_quantity, in_house_batch_no, performed_by, checked_by, remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''',
                            (
                                doc_id,
                                row.get("raw_material"),
                                row.get("unit"),
                                row.get("standard_quantity"),
                                row.get("allowed_range_min"),
                                row.get("allowed_range_max"),
                                row.get("actual_quantity"),
                                row.get("in_house_batch_no"),
                                row.get("performed_by"),
                                row.get("checked_by"),
                                row.get("remarks")
                            )
                        )
            except Exception as e:
                print(f"Failed to insert into material_usage_row: {{e}}")
        ```

        Use this example as guidance to generate functions for the schema '{schema_name}'. Ensure:
        - Proper SQLite syntax for table creation and relationships.
        - Use INSERT OR IGNORE or INSERT OR REPLACE to avoid duplicate row errors.
        - Handle nullable columns (`None`) and optional fields explicitly.
            - If using the Python join command, make sure that the field is of the appropriate type before performing the join.
        - DO NOT INCLUDE DUPLICATE COLUMNS IN THE TABLE.
        - Include necessary constraints and indexes to ensure data integrity.
        - Return **only valid Python code** for these two functions. Make sure to add all necessary package imports. Do NOT include explanations or comments.
        - Your code must be executable as is, and should not require any human debugging.
        """

        llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages).content
        return response.strip("```").lstrip("python").strip()

    def _save_script(self, filepath: str, code: str):
        """
        Save the generated Python script to the specified file.

        Args:
            filepath (str): Path to save the script.
            code (str): Python script code.
        """
        os.makedirs(SQL_SCRIPTS_DIR, exist_ok=True)
        with open(filepath, "w") as f:
            f.write(code)
        print(f"Script saved at {filepath}.")

    def _get_schema_code(self, schema_name: str) -> str:
        """
        Retrieve the code of the matched Pydantic schema.

        Args:
            schema_name (str): The name of the schema.

        Returns:
            str: The schema code as a string.
        """
        schema_path = os.path.join(SCHEMA_DIR, f"{schema_name}.py")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(
                f"Schema file for '{schema_name}' not found at {schema_path}."
            )

        with open(schema_path, "r") as file:
            schema_code = file.read()

        return schema_code


if __name__ == "__main__":
    loader = DynamicSQLLoader(DB_PATH)

    succeeded = []
    failed = []

    loader.clear_database()

    loader.create_doc_info_table()  # Create the doc_info table if it doesn't exist.

    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
            print(f"Processing file: {filename}")

            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Identify schema
                schema_name = loader.identify_schema(data)
                if not schema_name:
                    print(f"No matching schema found for {filename}.")
                    failed.append((filename, "No matching schema"))
                    continue

                print(f"Matched schema: {schema_name}")
                try:
                    schema_code = loader._get_schema_code(schema_name)
                except FileNotFoundError as e:
                    print(f"Schema file not found for {schema_name}: {e}")
                    failed.append((filename, "Schema file not found"))
                    continue

                # Ensure SQL script and execute
                loader.ensure_sql_script(schema_name, schema_code)

                # Create tables
                try:
                    loader.execute_sql_script(schema_name, "create_tables")
                except Exception as e:
                    print(f"Failed to create tables for {filename}: {e}")
                    failed.append((filename, "Could not create tables"))
                    continue

                # Resolve doc_id
                doc_id = loader.resolve_doc_id(filename)

                # Insert data
                try:
                    loader.execute_sql_script(schema_name, "insert_data", data, doc_id)
                    succeeded.append(filename)
                except sqlite3.IntegrityError as e:
                    print(f"Duplicate entry for {filename}: {e}")
                    failed.append((filename, "Duplicate entry"))
                except Exception as e:
                    print(f"Failed to insert data for {filename}: {e}")
                    failed.append((filename, "Could not insert data"))

            except Exception as e:
                print(f"Failed to process {filename}: {e}")
                failed.append((filename, str(e)))

    loader.close()

    print("\nProcessing Complete!")
    print(f"Succeeded: {len(succeeded)}")
    print(f"Failed: {len(failed)}\n")

    if succeeded:
        print("Successfully processed documents:")
        for doc in succeeded:
            print(f" - {doc}")

    if failed:
        print("\nFailed documents:")
        for doc, reason in failed:
            print(f" - {doc}: {reason}")
