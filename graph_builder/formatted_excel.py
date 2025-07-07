import hashlib
import pandas as pd
import shutil
from .utils import name_generator

async def main_excel_to_formatted_excel(excel_file):
    
    table_dict = {}

    # try loading the file
    try:
        xls = pd.ExcelFile(excel_file, engine="openpyxl")

    except Exception as e:

        # returning a dataframe contianing the error
        my_string = f"❌ Unexpected error: {e}"
        df = pd.DataFrame([f"{my_string}"], columns=["content"])
        print(my_string)

        # ending the function
        return df

    sheet_names = xls.sheet_names

    for given_name in sheet_names:
        
        table_hash= hashlib.md5(given_name.encode()).hexdigest()[:8]

        df_sheet = pd.read_excel(xls, sheet_name=given_name)

        # function that reads to create a new name
        new_name = name_generator(df_sheet)
        print(new_name)

        table_dict[table_hash] = {
            "given_name": given_name,
            "rename_name": new_name,
            "csv_data": df_sheet.to_csv(index=False)
        }
    
    # storing the dict into a summary excel
    # Destination file path
    intended_file = "extracted_tables.xlsx"

    # copying the file
    shutil.copyfile(excel_file, intended_file)

    # creating the summary table
    with pd.ExcelWriter(intended_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:

        # summary sheet
        summary_rows = [
            (table_hex_name, info["given_name"], info["rename_name"])
            for table_hex_name, info in table_dict.items()
        ]
        summary_df = pd.DataFrame(summary_rows, columns=["table_hash", "given_name", "rename_name"])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    # printing the summary table
    # Load the summary sheet back and print it
    summary = pd.read_excel(intended_file, sheet_name="Summary", engine="openpyxl")

    return summary
