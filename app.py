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
    return process_pdf_pages(filepath, document_type, page_numbers=pages)

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


@app.route("/api/status/<task_id>", methods=["GET"])
def task_status(task_id):
    task = process_pdf_task.AsyncResult(task_id)
    
    # Build the response object based on task state
    if task.state == "PENDING":
        response = {"state": "PENDING", "status": "Pending..."}
    elif task.state == "SUCCESS":
        response = {"state": "SUCCESS", "result": task.result}
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

@app.route("/chat", methods=["GET"])
def chat_interface():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json  # Get JSON data from the request
    user_message = data.get("message")  # Extract the user's message
    # Log the message for debugging
    print(f"User message: {user_message}")
    # Placeholder response
    return jsonify({"reply": "Message processed"})

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")  # Default to "0.0.0.0" if not set
    port = int(os.getenv("FLASK_PORT", 5002))  # Default to 5002 if not set
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"  # Default to True if not set
    app.run(host=host, port=port, debug=debug)