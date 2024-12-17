import json
import os
import sqlite3

from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(script_dir, ".env")
load_dotenv(ENV_PATH)

DB_PATH = os.getenv("SQL_DB_PATH", os.path.join(script_dir, "batch_data.db"))


class SQLDataLoader:
    def __init__(self, db_path):
        """
        Initializes the SQLite database loader.
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"Connected to database at: {self.db_path}")

    def close(self):
        """Closes the database connection."""
        self.conn.close()
        print("Database connection closed.")

    def create_tables(self):
        """Creates necessary tables for batch processing."""
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS batch_details (
            product_name TEXT,
            stage TEXT,
            batch_no TEXT PRIMARY KEY,
            batch_started_on TEXT,
            batch_completed_on TEXT
        )
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS material_usage_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_no TEXT,
            raw_material TEXT,
            unit TEXT,
            standard_quantity INTEGER,
            allowed_range_min INTEGER,
            allowed_range_max INTEGER,
            actual_quantity INTEGER,
            in_house_batch_no TEXT,
            performed_by TEXT,
            checked_by TEXT,
            remarks TEXT,
            quantity_within_range BOOLEAN,
            FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
        )
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS equipment_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_no TEXT,
            serial_no INTEGER,
            name TEXT,
            id_no TEXT,
            FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
        )
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS approval_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_no TEXT,
            prepared_by TEXT,
            reviewed_by TEXT,
            approved_by TEXT,
            FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
        )
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS document_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_no TEXT,
            revision_no TEXT,
            effective_date TEXT,
            mfr_ref_no TEXT,
            format_no TEXT,
            FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
        )
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS manufacturing_procedure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_no TEXT,
            op_no INTEGER,
            description TEXT,
            date TEXT,
            time_from TEXT,
            time_to TEXT,
            duration TEXT,
            performed_by TEXT,
            checked_by TEXT,
            remarks TEXT,
            FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
        )
        """
        )
        print("Tables created successfully.")

    def insert_data(self, json_file):
        """Inserts data into the database from a JSON file."""
        with open(json_file, "r") as f:
            data = json.load(f)

        batch_details = data["batch_details"]
        self.cursor.execute(
            """
        INSERT OR IGNORE INTO batch_details (product_name, stage, batch_no, batch_started_on, batch_completed_on)
        VALUES (?, ?, ?, ?, ?)
        """,
            (
                batch_details["product_name"],
                batch_details["stage"],
                batch_details["batch_no"],
                batch_details["batch_started_on"],
                batch_details["batch_completed_on"],
            ),
        )

        for material in data["material_usage_table"]["rows"]:
            self.cursor.execute(
                """
            INSERT INTO material_usage_table (batch_no, raw_material, unit, standard_quantity, allowed_range_min,
                                              allowed_range_max, actual_quantity, in_house_batch_no, performed_by,
                                              checked_by, remarks, quantity_within_range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    batch_details["batch_no"],
                    material["raw_material"],
                    material["unit"],
                    material["standard_quantity"],
                    material["allowed_range_min"],
                    material["allowed_range_max"],
                    material["actual_quantity"],
                    material["in_house_batch_no"],
                    material["performed_by"],
                    material["checked_by"],
                    material["remarks"],
                    material["quantity_within_range"],
                ),
            )

        for equipment in data["equipment_list"]["equipments"]:
            self.cursor.execute(
                """
            INSERT INTO equipment_list (batch_no, serial_no, name, id_no)
            VALUES (?, ?, ?, ?)
            """,
                (
                    batch_details["batch_no"],
                    equipment["serial_no"],
                    equipment["name"],
                    equipment["id_no"],
                ),
            )

        approval_details = data["approval_details"]
        self.cursor.execute(
            """
        INSERT INTO approval_details (batch_no, prepared_by, reviewed_by, approved_by)
        VALUES (?, ?, ?, ?)
        """,
            (
                batch_details["batch_no"],
                approval_details["prepared_by"],
                approval_details["reviewed_by"],
                approval_details["approved_by"],
            ),
        )

        document_metadata = data["document_metadata"]
        self.cursor.execute(
            """
        INSERT INTO document_metadata (batch_no, revision_no, effective_date, mfr_ref_no, format_no)
        VALUES (?, ?, ?, ?, ?)
        """,
            (
                batch_details["batch_no"],
                document_metadata["revision_no"],
                document_metadata["effective_date"],
                document_metadata["mfr_ref_no"],
                document_metadata["format_no"],
            ),
        )

        for step in data["manufacturing_procedure"]["steps"]:
            self.cursor.execute(
                """
            INSERT INTO manufacturing_procedure (batch_no, op_no, description, date, time_from, time_to, duration,
                                                 performed_by, checked_by, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    batch_details["batch_no"],
                    step["op_no"],
                    step["description"],
                    step["date"],
                    step["time_from"],
                    step["time_to"],
                    step["duration"],
                    step["performed_by"],
                    step["checked_by"],
                    step["remarks"],
                ),
            )

        print("Data inserted successfully.")
        self.conn.commit()


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    JSON_FILE_PATH = os.path.join(
        script_dir, "../knowledge_base/574 (1)_processed.json"
    )

    loader = SQLDataLoader(DB_PATH)
    loader.create_tables()
    loader.insert_data(JSON_FILE_PATH)
    loader.close()
    print("Database initialized and data loaded successfully.")
