# app.py
from celery import Celery
from flask import Flask, request, render_template, flash, jsonify
from src.processing import process_pdf_pages
from dotenv import load_dotenv
import json
import os
from threading import Lock
from schema_helper import SCHEMA_DIR, load_schema, save_schema, generate_schema_with_gpt, convert_pdf_to_images
from flask_cors import CORS
from agents.sql_agent.json_to_db import JSONToSQL
from agents.sql_agent.utils import (
    ensure_column_exists,
    insert_data,
)
from agents.controller_agent.controller import app as controller_app
import asyncio

load_dotenv()
app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
CORS(app, resources={r"/api/*": {"origins": "*"}})
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

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
        "app",
        backend="redis://localhost:6379/0",
        broker="redis://localhost:6379/0"
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery()

@celery.task
def process_pdf_task(filepath, pages, document_type):
    schema = load_schema(document_type)

    if not schema:
        # If schema does not exist, generate it dynamically
        print(f"Schema for document type '{document_type}' not found. Generating dynamically...")
        images = convert_pdf_to_images(filepath)  # Function to convert PDF to images
        schema_code = generate_schema_with_gpt(images, document_type)
        save_schema(document_type, schema_code)  # Save the generated schema
        print(f"Schema generated and saved for document type '{document_type}'.")


    print(f"Processing file: {filepath}, Document Type: {document_type}")
    result = process_pdf_pages(filepath, document_type, page_numbers=pages)
    return {"filename": os.path.basename(filepath), "data": result}

def parse_pages_input(pages_input):
    if not pages_input:
        return ""

    pages = []
    for part in pages_input.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages

# HTML Route for the Website
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", document_types=document_types)

# API Route for Document Upload
# @app.route("/api/document_process", methods=["POST"])
# def document_upload():
#     files = request.files.getlist("files[]")
#     document_types_selected = request.form.getlist("document_types[]")

#     if not files:
#         return jsonify({"error": "No files uploaded."}), 400

#     if len(files) != len(document_types_selected):
#         return jsonify({"error": "Each file must have a corresponding document type."}), 400

#     task_ids = []
#     for file, doc_type in zip(files, document_types_selected):
#         if file and file.filename.endswith(".pdf"):
#             filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
#             file.save(filepath)

#             # Trigger Celery task for each file
#             task = process_pdf_task.delay(filepath, [], doc_type)
#             task_ids.append(task.id)

#     return jsonify({"message": "Files uploaded successfully!", "task_ids": task_ids})

@app.route("/api/document_process", methods=["POST"])
def upload_document():
    file = request.files.get("file")
    doc_type = request.form.get("document_type")

    if not file or not doc_type:
        return jsonify({"error": "File and document type are required."}), 400

    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    # Save the file
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Trigger the Celery task
    task = process_pdf_task.delay(filepath, [], doc_type)

    # Return the task ID
    return jsonify({"message": "Document uploaded successfully!", "task_id": task.id}), 202


# @app.route("/api/status/<task_id>")
# def task_status(task_id):
#     task = process_pdf_task.AsyncResult(task_id)
#     if task.state == "PENDING":
#         response = {"state": task.state, "status": "Pending..."}
#     elif task.state == "SUCCESS":
#         response = {"state": task.state, "result": task.result}
#     elif task.state == "FAILURE":
#         response = {"state": task.state, "status": str(task.info)}
#     else:
#         response = {"state": task.state, "status": task.info}

#     return render_template("task_status.html", response=response)

DB_PATH = os.getenv("SQL_DB_PATH")

def json_to_sql(filename, json_data):
    loader = JSONToSQL(DB_PATH)

    doc_id = loader.resolve_doc_id(filename)
    loader.gather_schema("main_table", json_data)
    loader.create_tables_from_schema()
    insert_data(
        loader.cursor, "main_table", json_data, doc_id, ensure_column_exists
    )

    loader.commit()
    loader.close()

@app.route("/api/status/<task_id>", methods=["GET"])
def task_status(task_id):
    task = process_pdf_task.AsyncResult(task_id)
    
    # Build the response object based on task state
    if task.state == "PENDING":
        response = {"state": "PENDING", "status": "Pending..."}
    elif task.state == "SUCCESS":
        task_result = task.result
        filename = task_result.get("filename")
        json_data = task_result.get("data")
        if filename and json_data:
            json_to_sql(filename, json_data)
        response = {"state": "SUCCESS", "result": json_data}
    elif task.state == "FAILURE":
        response = {"state": "FAILURE", "error": str(task.info)}
    else:
        response = {"state": task.state, "status": task.info}

    return jsonify(response), 200

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
        state = loop.run_until_complete(controller_app.ainvoke({"user_input": user_message}, config=config))
        answer = state["final_answer"]
        # print(answer)
        # raw_json = answer.strip("```json").strip("```")        
        # parsed_data = json.loads(raw_json)
        # output = parsed_data.get("output")
        
        # Extract the response from the state
        response = {
            "answer": answer,
        }

        # Return the response to the user
        return jsonify(response), 200
    except Exception as e:
        # Handle errors gracefully
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5002, debug=True)
