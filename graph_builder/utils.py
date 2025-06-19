import fitz  # PyMuPDF
import os

# function that retrieves the graph of each image
def cropping_table(pdf_path, graph_name, polygon, page_number, dpi=300):

    # zero-based
    page_number = page_number - 1

    # making the saved folder
    save_folder = pdf_path.replace(".pdf", "")
    os.makedirs(save_folder, exist_ok=True) 

    output_image_path = save_folder + "/" + graph_name + ".png"

    # Open PDF
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)     

    # Get page size in PDF points (1 point = 1/72 inch)
    page_rect    = page.rect
    pdf_width    = page_rect.width
    pdf_height   = page_rect.height

    # Convert inches to points (1 inch = 72 points)
    page_width_pts = pdf_width * 72
    page_height_pts = pdf_height * 72

    # Convert normalized/relative coords to PDF points
    polygon_pts = [
        (polygon[0] / pdf_width * page_width_pts, polygon[1] / pdf_height * page_height_pts),
        (polygon[2] / pdf_width * page_width_pts, polygon[3] / pdf_height * page_height_pts),
        (polygon[4] / pdf_width * page_width_pts, polygon[5] / pdf_height * page_height_pts),
        (polygon[6] / pdf_width * page_width_pts, polygon[7] / pdf_height * page_height_pts),
    ]

    # Get bounding box from polygon
    xs, ys = zip(*polygon_pts)
    bbox = fitz.Rect(min(xs), min(ys), max(xs), max(ys))

    # Extracting from PDF
    pix = page.get_pixmap(clip=bbox, dpi=dpi)
    pix.save(output_image_path)

    print(f"Cropped region saved to: {output_image_path}")


import base64
from config import llm

# processing the image function
def process_image(image_path):

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    system_prompt = f"""
    You are a document parser. Your task is to extract **only one specific table** from the provided image and return it in clean, Excel-compatible CSV format.

    Your output must follow these strict formatting rules:

    1. Output the table in CSV fomrat immediately!
    3. Use a **single-line header row**:
    - Flatten multi-line headers if necessary.
    - If the table has multi-row headers (e.g., a category like "BLEU-CN" above columns like "OSS", "Proprietary", "p-value"), **flatten** them by **concatenating the parent and child header values** using a hyphen (`-`).
        For example:
        - "BLEU-CN" spanning "OSS", "Proprietary", and "p-value"
        → becomes:
        BLEU-CN-OSS, BLEU-CN-Proprietary, BLEU-CN-p-value

        Do this consistently for all multi-line or hierarchical headers.

    5. Format as **CSV only** (commas as delimiters). Do **not** use Markdown, tables, or extra formatting.
    6. For numbers with comma separators (e.g., "10,000"), replace the comma with a space: "10 000". **Do not** use commas inside numeric values.
    7. For string values that contain commas (e.g., "chicken, rice"), replace each comma with a underscore, like "chicken_rice". Do not use commas inside string values under any circumstance, as they will break the CSV format.
    8. Do **not** extract summaries, explain content, or rephrase. Your job is extraction only.
    9. Each row must contain the same number of columns. If any cell is empty, include a comma and write NaN in the field to preserve structure.
    10. Leave **one blank line** (`\n`) after the table for parsing.
    """

    message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": system_prompt,
            },
            {
                "type": "image",
                "source_type": "base64",
                "data": image_data,
                "mime_type": "image/jpeg",
            },
        ],
    }
    response = llm.invoke([message])

    return response.text()

# getting the a mini LLM to read the data
from langchain_core.messages import AIMessage


from config import llm_mini

# function that processes the csv file
def name_determiner(csv_file):
    
    main_prompt = table_usefulness_prompt(csv_file)
    main_prompt = AIMessage(content=main_prompt)
   
    response = llm_mini.invoke([main_prompt])

    return response.content
    ## True and false
    # if response contains True generate a table name from the csv data

    # else response contains false, remove from the dict

def table_usefulness_prompt(csv_file):
    return f"""You are an intelligent assistant. Your task is to determine whether the following CSV data is useful.

    - If the table contains structured, meaningful data that could be visualized or analyzed, respond with: TRUE
    - If the table appears empty, unstructured, repetitive, or non-informative, respond with: FALSE
    - Respond with only one word: TRUE or FALSE — no explanation, punctuation, or extra content.

    CSV Sample:
    {csv_file}
    """

def table_name_gnereator_prompt(csv_file):

    # retrieving the first 3 rows only so as to not feed the entire csv into the gpt model
    csv_lines = csv_file.strip().splitlines()
    csv_sample = "\n".join(csv_lines[:4]) 

    return f"""
    You are a smart assistant. Based on the following CSV sample, generate a short, meaningful name for the table.

    Instructions:
    - Respond with only the name — no explanation, no punctuation, and no formatting.
    - You may use spaces and line breaks freely in your response where appropriate.
    - Preserve the format and indentation of any input text shown.

    CSV Sample:
    {csv_sample}

    Table name:"""

# function that generates a name
def name_generator(csv_file):
    
    main_prompt = table_name_gnereator_prompt(csv_file)
    main_prompt = AIMessage(content=main_prompt)

    response = llm_mini.invoke([main_prompt])

    return response.content
