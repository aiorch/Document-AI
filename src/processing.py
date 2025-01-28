import json
import sys
import tiktoken

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import (ChatPromptTemplate, HumanMessagePromptTemplate,
                               SystemMessagePromptTemplate)
from langchain_openai import ChatOpenAI

from schemas.inspection_form import InspectionForm
from src.validation.material_usage import validate_material_usage
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
import time
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import importlib
# from azure.ai.documentintelligence import DocumentIntelligenceClient
from schema_helper import SCHEMA_DIR, load_schema


def error_exit(error_message):
    print(error_message)
    sys.exit(1)


# def extract_text_from_pdf_azure(file_path, pages_list=None):
#     # Retrieve endpoint and key from environment variables
#     endpoint = os.getenv("AZURE_DOC_ENDPOINT")
#     key = os.getenv("AZURE_DOC_KEY")

#     if not endpoint or not key:
#         raise ValueError("Azure Form Recognizer endpoint and key must be set in environment variables.")

#     # Initialize the Document Analysis Client
#     client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

#     # Read the PDF file
#     with open(file_path, "rb") as f:
#         document = f.read()

#     # Analyze the document using the 'prebuilt-read' model
#     poller = client.begin_analyze_document("prebuilt-read", document)
#     result = poller.result()

#     # Extract text from the analyzed document
#     extracted_text = ""
#     for page in result.pages:
#         for line in page.lines:
#             extracted_text += line.content + "\n"

#     return extracted_text

def extract_text_from_pdf_azure(file_path, pages_list=None):
    import os
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential

    # Retrieve endpoint and key from environment variables
    endpoint = os.getenv("AZURE_DOC_ENDPOINT")
    key = os.getenv("AZURE_DOC_KEY")

    if not endpoint or not key:
        raise ValueError("Azure Form Recognizer endpoint and key must be set in environment variables.")

    # Initialize the Document Analysis Client
    client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Read the PDF file
    with open(file_path, "rb") as f:
        document = f.read()

    # Analyze the document using the 'prebuilt-read' model
    poller = client.begin_analyze_document("prebuilt-read", document)
    result = poller.result()

    # Extract text and confidence scores from the analyzed document
    extracted_text = ""
    for page in result.pages:
        for word in page.words:
            extracted_text += f"{word.content} (Confidence: {word.confidence:.2f})\n"

    return extracted_text


def process_inspection_information(extracted_text, doc_type):
    try:
        schema_class = load_schema(doc_type)
    except ValueError as e:
        print(e)
        return {"error": str(e)}

    # Use LangChain’s Pydantic parser with the dynamically loaded schema
    parser = PydanticOutputParser(pydantic_object=schema_class)
    # TEMPORARY:Lists of names to fill in the "performed_by" and "checked_by" fields
    # Example list of names for "performed_by" and "checked_by" (one name per row in the table)
    names_performed_by = [
        "M. Praveen Reddy", "M. Praveen Reddy", "M. Praveen Reddy", "M. Praveen Reddy", "M. Praveen Reddy", "P. Venkatesh", "P. Venkatesh", "U. Sankara Rao", "U. Sankara Rao", "U. Sankara Rao", "Ravi Chatragadda", "Ravi Chatragadda", "Ravi Chatragadda", "G. Nithin Kumar", "K. Chinna Rao", "U. Sankara Rao"
    ]

    names_checked_by = [
        "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "S.K. Saidavali", "S.K. Saidavali", "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "K. Chinna Rao", "Amit Kumar", "A. Bala Swamy", "Ravi Chatragadda"
    ]


    # preamble = "This is a filled-out pharmaceutical inspection form. Extract relevant data accurately. IMPORTANT: Remember that the manufacturing procedure table spans multiple pages. Each word may have a confidence score attached to it from the OCR output. The input per word will be in this format: f"{word.content} (Confidence: {word.confidence:.2f})\n". Please format this correctly into the output json."
    # postamble = "Do not include any explanation in the reply; only include extracted information. This should be able to get decoded as json. The JSON must not contain syntax errors or incomplete structures. The pydantic structure given does not have to be followed rigidly. This means that if a table doesn't exist in the document, you don't need to create json for it in the output. Sometimes, the pydantic classes may be out of order and there could be multiple instances of a table. For each value in the json, attach a value below it with the confidence score"

    # preamble = """This is a filled-out pharmaceutical inspection form. Extract relevant data accurately. IMPORTANT: Remember that the manufacturing procedure table spans multiple pages. Each word may have a confidence score attached to it from the OCR output. The input per word will be in this format: "{word.content} (Confidence: {word.confidence:.2f})\n"."""
    preamble = """This is a filled-out pharmaceutical inspection form. Extract relevant data accurately. IMPORTANT: Remember that the manufacturing procedure table spans multiple pages. Each word may have a confidence score attached to it from the OCR output. The input per word will be in this format: "{word.content} (Confidence: {word.confidence:.2f})\n". When extracting data, group relevant words into fields and calculate the field-level confidence score as the average of the confidence scores of its constituent words."""

    # postamble = """Please ensure that the extracted data is structured in a valid JSON format. For each extracted value, include an associated confidence score. If certain tables or sections are missing from the document, omit them from the JSON output. The JSON must be free from syntax errors or incomplete structures. Do not include any explanation in the reply; only provide the extracted information."""
    postamble = """Please ensure that the extracted data is structured in a valid JSON format. For each field in the JSON, include the extracted value and its confidence score. If certain tables or sections are missing from the document, omit them from the JSON output. Ensure the JSON is free from syntax errors or incomplete structures. Do not include any explanation in the reply; only provide the extracted information."""

    system_message_prompt = SystemMessagePromptTemplate.from_template("{preamble}")
    human_message_prompt = HumanMessagePromptTemplate.from_template(
        "{format_instructions}\n\n{extracted_text}\n\n{postamble}"
    )

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    request = chat_prompt.format_prompt(
        preamble=preamble,
        format_instructions=parser.get_format_instructions(),
        extracted_text=extracted_text,
        postamble=postamble,
    ).to_messages()

    chat = ChatOpenAI(model="gpt-4o")
    response = chat.invoke(request, temperature=0.0)
    result = response.content
    result = result.strip().strip("```").replace("json\n", "", 1).strip()
    parsed_data = json.loads(result)
    if "material_usage_table" in parsed_data:
        parsed_data["material_usage_table"] = validate_material_usage(
            parsed_data["material_usage_table"]
        )
        # # Dynamically fill in "performed_by" and "checked_by" fields
        # parsed_data = dynamically_fill_fields(parsed_data, names_performed_by, names_checked_by)
        # Call the LLM-based function to update "performed_by" and "checked_by"
        parsed_data = process_inspection_information_with_llm(
            parsed_data, names_performed_by, names_checked_by
        )

    return parsed_data


def process_inspection_information_with_llm(json_data, names_performed_by, names_checked_by):
    """
    Use the LLM to update "performed_by" and "checked_by" fields in the JSON.
    Automatically cycle through the names if the list is not long enough.
    """
    # Initialize the ChatOpenAI model
    chat = ChatOpenAI(model="gpt-4o-2024-08-06")

    # Get the total number of rows to process
    rows = json_data.get("material_usage_table", {}).get("rows", [])
    total_rows = len(rows)

    # Extend the name lists by cycling through them if they are shorter than total rows
    if len(names_performed_by) < total_rows:
        names_performed_by = (names_performed_by * (total_rows // len(names_performed_by) + 1))[:total_rows]

    if len(names_checked_by) < total_rows:
        names_checked_by = (names_checked_by * (total_rows // len(names_checked_by) + 1))[:total_rows]

    # Create the LLM prompt
    prompt = f"""
    You are provided with a JSON extracted from a pharmaceutical batch record. The JSON contains multiple tables, each with rows and columns.

    Your task is to:
    1. Replace the "performed_by" and "checked_by" fields with names from the provided lists.
    2. Assign names sequentially from the lists, going row by row for each table.
    3. Ensure every "performed_by" field is assigned a name from the "performed_by" list, and every "checked_by" field is assigned a name from the "checked_by" list.
    4. If any value exists in the "performed_by" and "checked_by", it must be replaced with a name. Do NOT use "None".

    Here is the list of names for "performed_by":
    {names_performed_by}

    Here is the list of names for "checked_by":
    {names_checked_by}

    Below is the JSON to process:
    {json.dumps(json_data)}

    IMPORTANT: Return only the updated JSON. Do not include any explanations, comments, or additional text.
    """

    # Use SystemMessage for LangChain chat
    response = chat.invoke([SystemMessage(content=prompt)])
    result = response.content.strip().strip("```").replace("json\n", "", 1).strip()

    # Check if the result is empty
    if not result:
        print("Error: LLM returned an empty response.")
        error_exit("LLM returned an empty response. Check the prompt or LLM configuration.")

    # Try parsing the result and handle errors gracefully
    try:
        updated_json = json.loads(result)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from LLM response: {e}")
        print(f"LLM response: {result}")  # Log the raw response for debugging
        error_exit("Failed to decode JSON from LLM response.")

    # Parse the updated JSON and return it
    updated_json = json.loads(result)
    return updated_json

def save_processed_data(data, filename, directory):
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Saved processed data to {file_path}")

def process_pdf_pages(file_path, doc_type, page_numbers=[]):
    extracted_text = extract_text_from_pdf_azure(file_path, page_numbers)
    print(f"Extracted Text (Pages {page_numbers}):\n", extracted_text)
    response = process_inspection_information(extracted_text, doc_type)
    # response = process_inspection_information_with_chunking(extracted_text)
    print(f"Response from LLM:\n{response}")

    # Construct the path to the 'knowledge_base' directory within the 'agent' folder
    current_dir = os.path.dirname(os.path.abspath(__file__))

    knowledge_base_dir = os.path.join(current_dir, '..', 'agents', 'knowledge_base')
    # Normalize the path
    knowledge_base_dir = os.path.normpath(knowledge_base_dir)

    # Save the processed data
    filename = os.path.basename(file_path).replace(".pdf", "_processed.json")
    save_processed_data(response, filename, knowledge_base_dir)
    return response