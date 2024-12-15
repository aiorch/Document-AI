import json
import sqlite3
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "batch_data.db")

# Load JSON data
with open(os.path.join(script_dir, "../../knowledge_base/574 (1)_processed.json")) as f:
    data = json.load(f)

# Establish SQLite connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables

# Batch Details Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS batch_details (
    product_name TEXT,
    stage TEXT,
    batch_no TEXT PRIMARY KEY,
    batch_started_on TEXT,
    batch_completed_on TEXT
)
""")

# Material Usage Table
cursor.execute("""
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
""")

# Equipment List Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipment_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no TEXT,
    serial_no INTEGER,
    name TEXT,
    id_no TEXT,
    FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
)
""")

# Approval Details Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS approval_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no TEXT,
    prepared_by TEXT,
    reviewed_by TEXT,
    approved_by TEXT,
    FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
)
""")

# Document Metadata Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS document_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no TEXT,
    revision_no TEXT,
    effective_date TEXT,
    mfr_ref_no TEXT,
    format_no TEXT,
    FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
)
""")

# Raw Material Sheet Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS raw_material_sheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no TEXT,
    op_no INTEGER,
    initial_volume INTEGER,
    final_volume INTEGER,
    difference_volume INTEGER,
    FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
)
""")

# Manufacturing Procedure Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS manufacturing_procedure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no TEXT,
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
    FOREIGN KEY (batch_no) REFERENCES batch_details(batch_no)
)
""")

# Temperature Records Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS temperature_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_id INTEGER,
    time TEXT,
    temp_c REAL,
    sign TEXT,
    FOREIGN KEY (procedure_id) REFERENCES manufacturing_procedure(id)
)
""")

# Insert data into tables

# Insert Batch Details
batch_details = data["batch_details"]
cursor.execute("""
INSERT INTO batch_details (product_name, stage, batch_no, batch_started_on, batch_completed_on)
VALUES (?, ?, ?, ?, ?)
""", (batch_details["product_name"], batch_details["stage"], batch_details["batch_no"],
      batch_details["batch_started_on"], batch_details["batch_completed_on"]))

# Insert Material Usage Data
for material in data["material_usage_table"]["rows"]:
    cursor.execute("""
    INSERT INTO material_usage_table (batch_no, raw_material, unit, standard_quantity, allowed_range_min, 
                                      allowed_range_max, actual_quantity, in_house_batch_no, performed_by, 
                                      checked_by, remarks, quantity_within_range)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (batch_details["batch_no"], material["raw_material"], material["unit"], material["standard_quantity"],
          material["allowed_range_min"], material["allowed_range_max"], material["actual_quantity"],
          material["in_house_batch_no"], material["performed_by"], material["checked_by"],
          material["remarks"], material["quantity_within_range"]))

# Insert Equipment List
for equipment in data["equipment_list"]["equipments"]:
    cursor.execute("""
    INSERT INTO equipment_list (batch_no, serial_no, name, id_no)
    VALUES (?, ?, ?, ?)
    """, (batch_details["batch_no"], equipment["serial_no"], equipment["name"], equipment["id_no"]))

# Insert Approval Details
approval_details = data["approval_details"]
cursor.execute("""
INSERT INTO approval_details (batch_no, prepared_by, reviewed_by, approved_by)
VALUES (?, ?, ?, ?)
""", (batch_details["batch_no"], approval_details["prepared_by"], approval_details["reviewed_by"],
      approval_details["approved_by"]))

# Insert Document Metadata
document_metadata = data["document_metadata"]
cursor.execute("""
INSERT INTO document_metadata (batch_no, revision_no, effective_date, mfr_ref_no, format_no)
VALUES (?, ?, ?, ?, ?)
""", (batch_details["batch_no"], document_metadata["revision_no"], document_metadata["effective_date"],
      document_metadata["mfr_ref_no"], document_metadata["format_no"]))

# Insert Raw Material Sheet
for measurement in data["raw_material_sheet"]["measurements"]:
    cursor.execute("""
    INSERT INTO raw_material_sheet (batch_no, op_no, initial_volume, final_volume, difference_volume)
    VALUES (?, ?, ?, ?, ?)
    """, (batch_details["batch_no"], measurement["op_no"], measurement["initial_volume"],
          measurement["final_volume"], measurement["difference_volume"]))

# Insert Manufacturing Procedure and Temperature Records
for step in data["manufacturing_procedure"]["steps"]:
    cursor.execute("""
    INSERT INTO manufacturing_procedure (batch_no, op_no, description, equipment_no, date, time_from, time_to, 
                                         duration, performed_by, checked_by, remarks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (batch_details["batch_no"], step["op_no"], step["description"], step.get("equipment_no"),
          step["date"], step["time_from"], step["time_to"], step["duration"], step["performed_by"],
          step["checked_by"], step["remarks"]))

    # Get the last inserted procedure ID for linking temperature records
    procedure_id = cursor.lastrowid

    if step.get("temperature_records"):
        for record in step["temperature_records"]:
            cursor.execute("""
            INSERT INTO temperature_records (procedure_id, time, temp_c, sign)
            VALUES (?, ?, ?, ?)
            """, (procedure_id, record["time"], record["temp_c"], record["sign"]))

# Commit changes and close connection
conn.commit()
conn.close()

print("Data has been successfully inserted into the database.")
