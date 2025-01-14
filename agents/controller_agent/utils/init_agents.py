import os

from dotenv import load_dotenv

from agents.knowledge_graph_agent.langchain_graph_agent import GraphQAAgent
from agents.sql_agent.langchain_sql_agent import SQLQAAgent
from agents.workflow_agent.workflow_main import WorkflowAgent

# script_dir = os.path.dirname(os.path.abspath(__file__))
# ENV_PATH = os.path.join(script_dir, "../.env")
# load_dotenv(ENV_PATH, override=True)


def initialize_sql_agent():
    """Initialize the SQL Agent."""
    db_path = os.getenv("SQL_DB_PATH", "batch_data.db")
    llm_model = os.getenv("OPENAI_MODEL", "gpt-4")
    return SQLQAAgent(db_path=db_path, llm_model=llm_model)


def initialize_kg_agent():
    """Initialize the Knowledge Graph Agent."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")
    llm_model = os.getenv("OPENAI_MODEL", "gpt-4")
    try:
        return GraphQAAgent(
            uri=uri, username=username, password=password, llm_model=llm_model
        )
    except Exception as e:
        print("Could not initialize Knowledge Graph Agent due to Exception: %s" % e)
        return None


def initialize_workflow_agent():
    """Initialize the Workflow Agent."""
    return WorkflowAgent(
        os.getenv("SMTP_SERVER"),
        os.getenv("SMTP_PORT"),
        os.getenv("EMAIL_USER"),
        os.getenv("EMAIL_PASSWORD"),
        os.getenv("DEFAULT_RECIPIENT"),
    )
