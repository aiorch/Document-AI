# app.py
from flask import Flask, request, render_template, redirect, url_for, flash
import json
import os
from src.processing import process_pdf_pages

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

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
        # Check if a file is uploaded
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("No file selected!")
            return redirect(request.url)

        # Save the uploaded file
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        flash("File successfully uploaded")

        pages_input = request.form.get("pages")
        pages = parse_pages_input(pages_input)

        # Process the uploaded PDF using the LLM Whisperer function
        result = process_pdf_pages(filepath, page_numbers=pages)
        
        # Render result to the user
        return render_template("result.html", parsed_data=result)

    return render_template("index.html")

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5001, debug=True)
