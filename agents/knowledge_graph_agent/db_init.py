import json
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

script_dir = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(script_dir, ".env")
load_dotenv(ENV_PATH)

# Neo4j credentials
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")


class GraphDataLoader:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def load_json_to_graph(self, json_file):
        with open(json_file, "r") as f:
            data = json.load(f)

        with self.driver.session() as session:
            batch = data["batch_details"]
            session.write_transaction(self._create_batch_details, batch)

            for material in data["material_usage_table"]["rows"]:
                session.write_transaction(
                    self._create_material_usage, material, batch["batch_no"]
                )

            for equipment in data["equipment_list"]["equipments"]:
                session.write_transaction(
                    self._create_equipment, equipment, batch["batch_no"]
                )

            approval = data["approval_details"]
            session.write_transaction(
                self._create_approval_details, approval, batch["batch_no"]
            )

            document = data["document_metadata"]
            session.write_transaction(
                self._create_document_metadata, document, batch["batch_no"]
            )

            for sheet in data["raw_material_sheet"]["measurements"]:
                session.write_transaction(
                    self._create_raw_material_sheet, sheet, batch["batch_no"]
                )

            for step in data["manufacturing_procedure"]["steps"]:
                procedure_id = session.write_transaction(
                    self._create_manufacturing_step, step, batch["batch_no"]
                )

                if step.get("temperature_records"):
                    for record in step["temperature_records"]:
                        session.write_transaction(
                            self._create_temperature_record, record, procedure_id
                        )

            print("Data successfully loaded into Neo4j.")

    @staticmethod
    def _create_batch_details(tx, batch):
        query = """
        MERGE (b:Batch {batch_no: $batch_no})
        SET b.product_name = $product_name, b.stage = $stage,
            b.batch_started_on = $started_on, b.batch_completed_on = $completed_on
        """
        tx.run(
            query,
            batch_no=batch["batch_no"],
            product_name=batch["product_name"],
            stage=batch["stage"],
            started_on=batch["batch_started_on"],
            completed_on=batch["batch_completed_on"],
        )

    @staticmethod
    def _create_material_usage(tx, material, batch_no):
        query = """
        MERGE (m:Material {raw_material: $raw_material})
        SET m.actual_quantity = $actual_quantity,
            m.unit = $unit,
            m.allowed_range_min = $allowed_range_min,
            m.allowed_range_max = $allowed_range_max,
            m.quantity_within_range = $quantity_within_range
        MERGE (b:Batch {batch_no: $batch_no})
        MERGE (m)-[:USED_IN]->(b)
        """
        tx.run(
            query,
            raw_material=material["raw_material"],
            actual_quantity=material["actual_quantity"],
            unit=material["unit"],
            allowed_range_min=material["allowed_range_min"],
            allowed_range_max=material["allowed_range_max"],
            quantity_within_range=material["quantity_within_range"],
            batch_no=batch_no,
        )

    @staticmethod
    def _create_equipment(tx, equipment, batch_no):
        query = """
        MERGE (e:Equipment {id_no: $id_no})
        SET e.name = $name, e.serial_no = $serial_no
        MERGE (b:Batch {batch_no: $batch_no})
        MERGE (e)-[:USED_IN]->(b)
        """
        tx.run(
            query,
            id_no=equipment["id_no"],
            name=equipment["name"],
            serial_no=equipment["serial_no"],
            batch_no=batch_no,
        )

    @staticmethod
    def _create_approval_details(tx, approval, batch_no):
        query = """
        MERGE (a:Approval {prepared_by: $prepared_by, reviewed_by: $reviewed_by, approved_by: $approved_by})
        MERGE (b:Batch {batch_no: $batch_no})
        MERGE (a)-[:APPROVES]->(b)
        """
        tx.run(
            query,
            prepared_by=approval["prepared_by"],
            reviewed_by=approval["reviewed_by"],
            approved_by=approval["approved_by"],
            batch_no=batch_no,
        )

    @staticmethod
    def _create_document_metadata(tx, document, batch_no):
        query = """
        MERGE (d:Document {revision_no: $revision_no})
        SET d.effective_date = $effective_date, d.mfr_ref_no = $mfr_ref_no, d.format_no = $format_no
        MERGE (b:Batch {batch_no: $batch_no})
        MERGE (d)-[:ASSOCIATED_WITH]->(b)
        """
        tx.run(
            query,
            revision_no=document["revision_no"],
            effective_date=document["effective_date"],
            mfr_ref_no=document["mfr_ref_no"],
            format_no=document["format_no"],
            batch_no=batch_no,
        )

    @staticmethod
    def _create_raw_material_sheet(tx, sheet, batch_no):
        query = """
        MERGE (r:RawMaterialSheet {op_no: $op_no})
        SET r.initial_volume = $initial_volume, r.final_volume = $final_volume, r.difference_volume = $difference_volume
        MERGE (b:Batch {batch_no: $batch_no})
        MERGE (r)-[:RELATED_TO]->(b)
        """
        tx.run(
            query,
            op_no=sheet["op_no"],
            initial_volume=sheet["initial_volume"],
            final_volume=sheet["final_volume"],
            difference_volume=sheet["difference_volume"],
            batch_no=batch_no,
        )

    @staticmethod
    def _create_manufacturing_step(tx, step, batch_no):
        query = """
        CREATE (s:ManufacturingStep {description: $description, op_no: $op_no})
        SET s.date = $date, s.time_from = $time_from, s.time_to = $time_to,
            s.duration = $duration, s.performed_by = $performed_by, s.checked_by = $checked_by
        MERGE (b:Batch {batch_no: $batch_no})
        MERGE (s)-[:PART_OF]->(b)
        RETURN id(s) AS step_id
        """
        result = tx.run(
            query,
            op_no=step["op_no"],
            description=step["description"],
            date=step["date"],
            time_from=step["time_from"],
            time_to=step["time_to"],
            duration=step["duration"],
            performed_by=step["performed_by"],
            checked_by=step["checked_by"],
            batch_no=batch_no,
        )
        return result.single()["step_id"]

    @staticmethod
    def _create_temperature_record(tx, record, procedure_id):
        query = """
        MATCH (s)
        WHERE id(s) = $procedure_id
        CREATE (t:TemperatureRecord {time: $time, temp_c: $temp_c, sign: $sign})
        MERGE (t)-[:MEASURED_AT]->(s)
        """
        tx.run(
            query,
            procedure_id=procedure_id,
            time=record["time"],
            temp_c=record["temp_c"],
            sign=record["sign"],
        )


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    KB_JSON_FILE_PATH = os.path.join(
        script_dir, "../knowledge_base/574 (1)_processed.json"
    )
    loader = GraphDataLoader(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    loader.load_json_to_graph(KB_JSON_FILE_PATH)
    loader.close()
    print("Neo4j graph initialized with data.")
