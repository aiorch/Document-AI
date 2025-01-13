import os 
import json
from langchain.schema import SystemMessage
from langchain_openai import ChatOpenAI
from pdf2image import convert_from_path
from PIL import Image
import io 
import base64
from openai import OpenAI
import importlib

SCHEMA_DIR = "schemas"

def convert_pdf_to_images(filepath):
    try:
        images = convert_from_path(filepath)
        image_data = []

        for idx, image in enumerate(images):
            img_byte_array = io.BytesIO()
            image.save(img_byte_array, format="PNG")
            img_byte_array.seek(0)
            image_data.append(img_byte_array.read())

            # Save the image locally for debugging
            image.save(f"debug_page_{idx + 1}.png", format="PNG")

        return image_data
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images: {e}")

def load_schema(document_type):
    schema_path = os.path.join(SCHEMA_DIR, f"{document_type}.py")
    if not os.path.exists(schema_path):
        print(f"Schema for '{document_type}' not found.")
        return None

    # Dynamically load the schema module
    module_name = f"schemas.{document_type}"
    spec = importlib.util.spec_from_file_location(module_name, schema_path)
    print("spec")
    print(spec)
    schema_module = importlib.util.module_from_spec(spec)
    print("schema module")
    print(schema_module)
    spec.loader.exec_module(schema_module)

    # Correctly derive the class name based on the document_type
    schema_class_name = document_type.replace("_", " ").title().replace(" ", "")
    print("schema class name")
    print(schema_class_name)
    schema_class = getattr(schema_module, schema_class_name, None)
    if not schema_class:
        raise ValueError(f"Schema class '{schema_class_name}' not found in '{document_type}.py'.")
    
    return schema_class


def save_schema(document_type, schema_code):
    os.makedirs(SCHEMA_DIR, exist_ok=True)
    schema_path = os.path.join(SCHEMA_DIR, f"{document_type}.py")
    
    with open(schema_path, "w") as f:
        f.write(schema_code)
    
    print(f"Schema for '{document_type}' saved to {schema_path}.")


def generate_schema_with_gpt(image_data_list, document_type):
    page_schemas = []
    imports = set()
    client = OpenAI()

    for idx, image_data in enumerate(image_data_list):
        try:
            print(f"Processing page {idx + 1}...")

            # Convert image data to base64
            img_str = base64.b64encode(image_data).decode()

            # Prepare the prompt
            prompt = f"""
        You are provided with an image of page {idx + 1} of a document coming from the work logs of a Chemical factory. 
        Your task is to create a Pydantic schema that represents the structure of this document type.
        
        The schema should have:
        - A top-level model named '{document_type.capitalize()}Page{idx + 1}'.
        - Each field should have an appropriate type, e.g., `str`, `int`, or `list[<sub-model>]`.
        - Use optional fields mostly to account for cases where data might be missing.

        Return the schema in valid Python code with imports. Do NOT include explanations or comments.

        Image:
        <base64 encoded image>
        """

            # Send request to GPT-4 Vision
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{img_str}"}
                            }
                        ]
                    }
                ]
            )

            schema_code = response.choices[0].message.content.strip().strip("```")
            page_schemas.append(schema_code)
            print(f"Schema for page {idx + 1} generated successfully.")

            # Extract imports from schema
            for line in schema_code.splitlines():
                if line.startswith("from") or line.startswith("import"):
                    imports.add(line)

        except Exception as e:
            print(f"Error processing page {idx + 1}: {e}")
            continue

    # Combine all schemas and create a top-level class
    top_level_schema = create_top_level_class(
        document_type, page_schemas, imports
    )
    return top_level_schema


def create_top_level_class(document_type, page_schemas, imports):
    # Consolidate all imports (remove duplicates)
    imports_section = "\n".join(sorted(set(imports)))

    # Define the top-level class
    top_level_class = f"class {document_type.capitalize()}(BaseModel):\n"

    # Add each page schema as a nested field
    for idx, schema in enumerate(page_schemas, start=1):
        page_class_name = f"{document_type.capitalize()}Page{idx}"
        top_level_class += f"    page_{idx}: Optional[{page_class_name}] = None\n"

    # Combine everything into the final schema
    combined_schema = (
        f"{imports_section}\n\n"
        + "\n\n".join(page_schemas)  # Use concatenation to avoid nesting f-strings
        + f"\n\n{top_level_class}"
    )

    # Ensure there are no unnecessary markers
    combined_schema = combined_schema.replace("python\n", "").replace("python", "")

    return combined_schema