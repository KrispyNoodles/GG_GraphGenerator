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


from typing import List

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from graph_builder.csv_to_graph import generate_code


class CustomTableRetriever(BaseRetriever):
    base_retriever: BaseRetriever
    """
    A custom retriever that returns a code string to generate a visualization 
    based on the most relevant table retrieved for a user's query.

    This retriever uses a base retriever (e.g., TFIDFRetriever) to locate the most 
    relevant table from preloaded documents. It then generates Python code using 
    the associated DataFrame and user query.

    Only the synchronous method `_get_relevant_documents` is implemented. 
    If the retrieval logic involves I/O operations (e.g., file or network access), 
    implementing the asynchronous `_aget_relevant_documents` may provide performance benefits.

    The default async interface will still work by executing the sync method in a thread.
    """
    
    # the function that retrieves the code
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        
        # retrieving the specific searctr
        result = self.base_retriever.invoke(query)

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
    

def create_retriever(document_array):

    retriever = TFIDFRetriever.from_documents(document_array, k=1)
        
    custom_retriever = CustomTableRetriever(base_retriever=retriever)

    retriever_tool = create_retriever_tool(
        retriever=custom_retriever,
        name="table_visualizer",
        description="Retrieve the Python code to be visualized based on the user's request."
    )

    return retriever_tool
