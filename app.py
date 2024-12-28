# app.py
from celery import Celery
from flask import Flask, request, render_template, flash
from src.processing import process_pdf_pages
from dotenv import load_dotenv
import json
import os
from threading import Lock
from schema_helper import SCHEMA_DIR, load_schema, save_schema, generate_schema_with_gpt, convert_pdf_to_images

load_dotenv()
app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
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

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        files = request.files.getlist("files[]")
        document_types_selected = request.form.getlist("document_types[]")

        if not files:
            flash("No files uploaded.")
            return render_template("index.html", document_types=document_types)

        if len(files) != len(document_types_selected):
            flash("Each file must have a corresponding document type.")
            return render_template("index.html", document_types=document_types)

        task_ids = []
        for file, doc_type in zip(files, document_types_selected):
            if file and file.filename.endswith(".pdf"):
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(filepath)

                # Trigger Celery task for each file
                task = process_pdf_task.delay(filepath, [], doc_type)
                task_ids.append(task.id)
                flash(f"Task created for file: {file.filename} with document type: {doc_type}")

        flash("All files uploaded and tasks created successfully!")
        return render_template("index.html", document_types=document_types, task_ids=task_ids)

    return render_template("index.html", document_types=document_types)

@app.route("/status/<task_id>")
def task_status(task_id):
    task = process_pdf_task.AsyncResult(task_id)
    if task.state == "PENDING":
        response = {"state": task.state, "status": "Pending..."}
    elif task.state == "SUCCESS":
        response = {"state": task.state, "result": task.result}
    elif task.state == "FAILURE":
        response = {"state": task.state, "status": str(task.info)}
    else:
        response = {"state": task.state, "status": task.info}

    return render_template("task_status.html", response=response)

@app.route("/add_document_type", methods=["POST"])
def add_document_type():
    new_type = request.form.get("document_type")
    if not new_type or new_type in document_types:
        flash("Invalid or duplicate document type.")
        return render_template("index.html", document_types=document_types)

    document_types.append(new_type)
    save_document_types(document_types)
    flash(f"Document type '{new_type}' added successfully!")
    return render_template("index.html", document_types=document_types)

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5001, debug=True)
