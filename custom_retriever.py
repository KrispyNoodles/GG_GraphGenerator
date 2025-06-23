from langchain.tools.retriever import create_retriever_tool
from langchain_community.retrievers import TFIDFRetriever

# creating a dataframe from the excel for the retriever
from langchain_core.documents import Document
import pandas as pd

def excel_to_df(excel_file_path):

    document_array = []

    # Read the entire Excel file
    xls = pd.ExcelFile(excel_file_path)

    # Read a specific sheet, for example "Summary"
    df = pd.read_excel(xls, sheet_name="Summary")

    # for each row in the dataframe
    for _, row in df.iterrows():

        # name of table being processed
        table_name = row["table_name"]
        print(f"Processing table: {row['full_name']}")

        # dataframe of the 
        table_df = pd.read_excel(xls, sheet_name=table_name)

        document_array.append(Document(page_content=row['full_name'],
                            metadata={"table_name":table_name,
                                        "page_no": row['page_no'],
                                        "dataframe": table_df
                                        })
                            )
        
    return document_array


document_array = excel_to_df("/home/ljunfeng/prototyping/extracted_tables.xlsx")
retriever = TFIDFRetriever.from_documents(document_array, k=1)


from typing import List

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from graph_builder.csv_to_graph import generate_code


class CustomTableRetriever(BaseRetriever):
    """A toy retriever that contains the top k documents that contain the user query.

    This retriever only implements the sync method _get_relevant_documents.

    If the retriever were to involve file access or network access, it could benefit
    from a native async implementation of `_aget_relevant_documents`.

    As usual, with Runnables, there's a default async implementation that's provided
    that delegates to the sync implementation running on another thread.
    """
    
    # the function that retrieves the code
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:

        # retrieving the specific searctr
        result = retriever.invoke(query)

        # if results cant be found
        if not result:
            return [Document(page_content="No relevant table found.", metadata={})]

        # retreiving the dataframe
        current_df = result[0].metadata["dataframe"]
        
        # retrieving the user's query
        user_request = query
        
        table_name = result[0].page_content

        # code to be run
        code_to_be_run = generate_code(current_df, user_request, table_name)
        
        # sending the code that was ran back to the llm
        return [Document(page_content=code_to_be_run, metadata={"table_name": table_name})]
    
custom_retriever = CustomTableRetriever(base_retriever=retriever)

retriever_tool = create_retriever_tool(
    retriever=custom_retriever,
    name="custom_table_code_runner",
    description="Searches for the relevant table and returns visualization code run based on user's query."
)