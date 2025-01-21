# app.py
import asyncio
import json
import os
from threading import Lock
from typing import Optional

import openai
from celery import Celery
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, render_template, request
from flask_cors import CORS
from openai import OpenAI

from agents.controller_agent.controller import app as controller_app
from agents.knowledge_graph_agent.json_to_db import JSONToKnowledgeGraph
from agents.sql_agent.json_to_db import JSONToSQL
from agents.sql_agent.utils import ensure_column_exists, insert_data
from schema_helper import (
    SCHEMA_DIR,
    convert_pdf_to_images,
    generate_schema_with_gpt,
    load_schema,
    save_schema,
)
from src.processing import process_pdf_pages

load_dotenv()
app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
CORS(app, resources={r"/api/*": {"origins": "*"}})
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
openai.api_key = os.getenv("OPENAI_API_KEY")

DOCUMENT_TYPES_FILE = "document_types.json"

# Load document types from file
def load_document_types():
    if not os.path.exists(DOCUMENT_TYPES_FILE):
        # Create the file with default types if it doesn't exist
        with open(DOCUMENT_TYPES_FILE, "w") as f:
            json.dump(["inspection_form", "invoice", "report"], f)
    with open(DOCUMENT_TYPES_FILE, "r") as f:
        return json.load(f)


file_lock = Lock()


def save_document_types(document_types):
    with file_lock:  # Ensure thread-safe writes
        with open(DOCUMENT_TYPES_FILE, "w") as f:
            json.dump(document_types, f)


# Load document types at startup
document_types = load_document_types()


def make_celery():
    celery = Celery(
        "app", backend="redis://localhost:6379/0", broker="redis://localhost:6379/0"
    )
    celery.conf.update(app.config)
    return celery


celery = make_celery()


@celery.task
def process_pdf_task(filepath, pages, document_type):
    schema = load_schema(document_type)

    if not schema:
        # If schema does not exist, generate it dynamically
        print(
            f"Schema for document type '{document_type}' not found. Generating dynamically..."
        )
        images = convert_pdf_to_images(filepath)  # Function to convert PDF to images
        schema_code = generate_schema_with_gpt(images, document_type)
        save_schema(document_type, schema_code)  # Save the generated schema
        print(f"Schema generated and saved for document type '{document_type}'.")

    print(f"Processing file: {filepath}, Document Type: {document_type}")
    result = process_pdf_pages(filepath, document_type, page_numbers=pages)
    filename = os.path.basename(filepath)
    if result:
        json_to_sql(filename, result)
        json_to_kg(filename, result)
    return {"filename": filename, "data": result}


def parse_pages_input(pages_input):
    if not pages_input:
        return ""

    pages = []
    for part in pages_input.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages


# HTML Route for the Website
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", document_types=document_types)


@app.route("/api/document_process", methods=["POST"])
def upload_document():
    file = request.files.get("file")
    doc_type = request.form.get("document_type")

    if not file or not doc_type:
        return jsonify({"error": "File and document type are required."}), 400

    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    # Preprocess the document type
    doc_type = doc_type.strip().lower().replace(" ", "_")

    # Save the file
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Trigger the Celery task
    task = process_pdf_task.delay(filepath, [], doc_type)

    # Return the task ID
    return (
        jsonify({"message": "Document uploaded successfully!", "task_id": task.id}),
        202,
    )


DB_PATH = os.getenv("SQL_DB_PATH")


def json_to_sql(filename, json_data):
    loader = JSONToSQL(DB_PATH)

    doc_id = loader.resolve_doc_id(filename)
    loader.gather_schema("main_table", json_data)
    loader.create_tables_from_schema()
    insert_data(loader.cursor, "main_table", json_data, doc_id, ensure_column_exists)

    loader.commit()
    loader.close()


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")


def json_to_kg(filename, json_data):
    loader = JSONToKnowledgeGraph(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    loader._process_single_document(json_data, filename)
    loader.close()


@app.route("/api/status/<task_id>", methods=["GET"])
def task_status(task_id):
    task = process_pdf_task.AsyncResult(task_id)

    # Build the response object based on task state
    if task.state == "PENDING":
        response = {"state": "PENDING", "status": "Pending..."}
    elif task.state == "SUCCESS":
        response = {"state": "SUCCESS", "result": json_data}
    elif task.state == "FAILURE":
        response = {"state": "FAILURE", "error": str(task.info)}
    else:
        response = {"state": task.state, "status": task.info}

    return jsonify(response), 200


client = OpenAI()  # Assumes OPENAI_API_KEY is set in environment variables


@app.route("/api/enhance_prompt", methods=["POST"])
def enhance_prompt():
    """
    Enhance the input prompt to make it effective for a SQL agent that
    will use another LLM for text-to-SQL conversion and database extraction.
    """
    data = request.json
    prompt: Optional[str] = data.get("prompt")

    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    try:
        # Define the system message to instruct the model
        system_message = (
            "You are an assistant that enhances user prompts intended for a SQL agent. "
            "The SQL agent will use another LLM to convert text to SQL queries and extract data from a SQL database. "
            "Your task is to make the user's prompt as effective as possible for this scenario."
            "DO NOT respond with any questions. Do the best you can in formulating a better prompt that the user can use."
        )

        # Call the OpenAI API using the new client
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        # Extract the enhanced prompt from the response
        enhanced_prompt = response.choices[0].message.content.strip()

        return jsonify({"enhanced_prompt": enhanced_prompt}), 200

    except Exception as e:
        print(f"Error while enhancing prompt: {e}")
        return jsonify({"error": "Failed to enhance prompt.", "details": str(e)}), 500


@app.route("/api/add_document_type", methods=["POST"])
def add_document_type():
    new_type = request.form.get("document_type")
    if not new_type or new_type in document_types:
        flash("Invalid or duplicate document type.")
        return render_template("index.html", document_types=document_types)

    document_types.append(new_type)
    save_document_types(document_types)
    flash(f"Document type '{new_type}' added successfully!")
    return render_template("index.html", document_types=document_types)


@app.route("/api/chat_process", methods=["GET"])
def chat_interface():
    return render_template("chat.html")


@app.route("/api/chat_process", methods=["POST"])
def chat():
    data = request.json
    print(f"Data: {data}")
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Log the user's message
    print(f"User message: {user_message}")

    # Prepare configuration for the controller agent
    config = {"configurable": {"thread_id": "workflow-thread"}}

    try:
        # Invoke the controller agent's app with the user input
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        state = loop.run_until_complete(
            controller_app.ainvoke({"user_input": user_message}, config=config)
        )
        answer = state["final_answer"]

        # Extract the response from the state
        print("Answer: {}".format(answer))
        response = {
            "answer": answer,
        }

        # Return the response to the user
        return jsonify(response), 200
    except Exception as e:
        # Handle errors gracefully
        print(f"Error: {e}")
        return (
            jsonify({"error": "An error occurred while processing your request"}),
            500,
        )


@app.route("/api/run_workflow", methods=["POST"])
def run_workflow():
    data = request.json
    workflow_name = data.get("workflow_name")
    workflow_rule = data.get("rule")
    email_list = data.get("email_list")

    if not workflow_name or not workflow_rule:
        return jsonify({"error": "Both 'workflow_name' and 'rule' are required."}), 400

    cwd = os.getcwd()
    workflows_file = os.path.join(cwd, "agents", "workflow_agent", "workflows.json")

    # Load existing workflows
    if not os.path.exists(workflows_file):
        with open(workflows_file, "w") as wf:
            json.dump({}, wf)  # Initialize as empty JSON

    with open(workflows_file, "r") as wf:
        workflows = json.load(wf)

    config = {"configurable": {"thread_id": "workflow-thread"}}

    # Check if workflow exists
    if workflow_name not in workflows:
        create_prompt = f"Create a workflow called {workflow_name} {workflow_rule} with email list {email_list}"
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            state = loop.run_until_complete(
                controller_app.ainvoke({"user_input": create_prompt}, config=config)
            )
            print(state["final_answer"])
        except Exception as e:
            print(state["final_answer"])
            return (
                jsonify({"error": "An error occurred while processing the workflow."}),
                500,
            )

    run_prompt = f"run workflow {workflow_name}"
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        state = loop.run_until_complete(
            controller_app.ainvoke({"user_input": run_prompt}, config=config)
        )
        # Parse the result
        final_result = state.get("final_result")
        if "condition failed" in final_result:
            # Workflow condition failed
            return jsonify({"message": final_result}), 422
        else:
            # Workflow executed successfully
            return jsonify({"message": final_result}), 200
    except Exception as e:
        # Handle other errors
        print(f"Error running workflow: {e}")
        return (
            jsonify({"error": "An error occurred while processing the workflow."}),
            500,
        )


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")  # Default to "0.0.0.0" if not set
    port = int(os.getenv("FLASK_PORT", 5002))  # Default to 5002 if not set
    debug = (
        os.getenv("FLASK_DEBUG", "True").lower() == "true"
    )  # Default to True if not set
    app.run(host=host, port=port, debug=debug)
