import hashlib
import uuid
import pandas as pd
from io import StringIO
from .utils import cropping_table, process_image
from azure.ai.documentintelligence.models import AnalyzeResult
from config import document_intelligence_client

## my own pdf
# pdf_path = "./dataset/ESD testing report and cert 2023.pdf"

# output of excel sheet
# output_excel_path = pdf_path.replace(".pdf","") + "/extracted_tables.xlsx"

async def main_pdf_to_csv(pdf_path):

    # output of excel sheet
    output_excel_path = pdf_path.replace(".pdf","") + "/extracted_tables.xlsx"

    table_dict = {}

    ## Document Intelligence
    with open(pdf_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document("prebuilt-layout", body=f)
    result: AnalyzeResult = poller.result()

    for i in result.tables:

        # retrieving the page_number_variable
        table_page = i.bounding_regions[0].page_number

        # if rowcount or columncount less than 3 then do not add them in
        if i.row_count <= 2 or i.column_count <= 2:
            continue

        # checking if the caption exits for each result in the table
        if i.caption:
            table_name = i.caption.content + "_" + str(table_page)
            table_hash = hashlib.md5(table_name.encode()).hexdigest()[:8]
            table_hash = "table_" + str(table_hash) + "_" + str(table_page)
        
        # if not it will be assigned a random name
        table_name = f"Unnamed_Table_{uuid.uuid4().hex[:8]}_{table_page}"
        table_hash = table_name
        
        table_polygon = i.bounding_regions[0].polygon
        
        # Storing the polygon and page into a dict
        table_dict[table_hash] = {
            "page_no": table_page,
            "polygon_shape": table_polygon,
            "full_name": table_name
        }
        
    # looping through the different tables to retrieving the image from the PDF and convert it into a csv
    for graph_name in table_dict:

        print(f"Retrieving Image for Graph: {graph_name}")
        
        page_number = table_dict[graph_name]["page_no"]
        polygon = table_dict[graph_name]["polygon_shape"]
        
        # cropping the image
        cropping_table(pdf_path, graph_name, polygon, page_number)

        # Retrieving the iamge path
        image_path = pdf_path.replace(".pdf","") + "/" +  graph_name + ".png"

        # converting the image to csv and storing it inot the dict
        response = process_image(image_path)
        table_dict[graph_name]["csv_data"] = response

    # Storing the excel
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:

        # summary sheet
        summary_rows = [
            (table_name, info["full_name"], info["page_no"])
            for table_name, info in table_dict.items()
        ]
        summary_df = pd.DataFrame(summary_rows, columns=["table_name", "full_name", "page_no"])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)


        # reading the csv data of each table into the excel
        for table_name in table_dict:
            
            sheet_name = table_name
            csv_text = table_dict[table_name]["csv_data"]

            df = pd.read_csv(StringIO(csv_text.strip()))
            df.to_excel(writer, sheet_name=sheet_name.strip(), index=False)

# calling the function
# main(pdf_path, output_excel_path)