import json
import os
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

from agents.knowledge_graph_agent.utils import (
    attach_all_descendants,
    create_or_merge_json_node,
    create_relationship,
    merge_document_node,
)

script_dir = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(script_dir, ".env")
load_dotenv(ENV_PATH)

# Neo4j credentials
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")

KNOWLEDGE_BASE_DIR = os.path.join(script_dir, "../knowledge_base")


class DynamicKnowledgeGraphLoader:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def ingest_directory(self, directory: str):
        files_processed = 0
        for filename in os.listdir(directory):
            if filename.lower().endswith(".json"):
                file_path = os.path.join(directory, filename)
                print(f"\n[PROCESSING]: {filename}")
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._process_single_document(data, filename)
                files_processed += 1

        print(f"\n[INFO] Finished ingestion of {files_processed} JSON file(s).")

    def _process_single_document(self, data: Any, doc_name: str):
        with self.driver.session() as session:
            doc_id = session.execute_write(merge_document_node, doc_name)

            root_uuid = session.execute_write(
                create_or_merge_json_node, data, None, None, 0, doc_name
            )

            session.execute_write(
                create_relationship, doc_id, "Document", root_uuid, "JsonNode", "HAS"
            )

            attach_all_descendants(session, doc_id, root_uuid)


if __name__ == "__main__":
    with GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    ) as driver:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("Deleted all existing data from Neo4j. Starting fresh.")

    loader = DynamicKnowledgeGraphLoader(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    loader.ingest_directory(KNOWLEDGE_BASE_DIR)
    loader.close()
    print("\n[ALL DONE] Knowledge graph ingestion complete!")
