# from csv_to_graph.prompts import SYSTEM_GRAPH_GENERATOR_PROMPT
# from pdf_to_graph.config import llm

from langchain.schema import HumanMessage, AIMessage
import pandas as pd
import re

from langchain_openai import AzureChatOpenAI
from dotenv import dotenv_values

config = dotenv_values("/home/ljunfeng/.env")

API_KEY=config.get("API_KEY")
API_ENDPOINT=config.get("ENDPOINT")
API_MODEL=config.get("MODEL")

# Initialize the LLM
llm = AzureChatOpenAI(
                model=API_MODEL, 
                openai_api_version="2024-05-01-preview",
                temperature=0,
                api_key= API_KEY,
                azure_endpoint=API_ENDPOINT
                )

# GRAPH PROMPTING
def get_graph_prompt(table_name):
    return f"""
    You are a highly skilled senior Python developer and graph-generating assistant. Your task is to generate clean, efficient, and bug-free Python code to create scientific graphs based on the user's request and input dataframe.

    You must follow these constraints and expectations:
    - Do not include any explanations or markdown formatting outside the specified sections.
    - If the user's request is ambiguous, ask a clarifying question before generating code.
    - Use `matplotlib` only for display and layout enhancements.
    - Include an appropriate title and legend if needed.
    - Do not create any functions
    - Plot only a single graph

    Format your response exactly as follows:
    ## START CODE
    Include:
    1. All imports (if any).
    2. Definition of the input dataframe.
    3. The code to create the specific graph.
    4. A call to the code to generate the graph.
    5. Save the graph as 'graph.png'
    6. do not incude ```python``` in this block.
    ## END CODE

    ## RESPONSE
    Provide the response to the user here
    ## END RESPONSE

    """

# User request feasibility + code generation
def generate_code(dataframe, user_request, table_name):

    # adjusted_user's message
    prompt = f"{user_request} This is the dataset: {dataframe}"

    message = [AIMessage(content=get_graph_prompt(table_name)), HumanMessage(content=prompt)]

    response = llm.invoke(message)

    if "import" in response.content and "plt" in response.content:
        
        code_block, response_text = extract_code_and_response(response.content)
        # print(f"code genereated is {code_block}")
        # exec(code_block)
        return code_block
    
    return "Graph not managed to be generated"   

# checking for code needs to be extracted
# checking for code needs to be extracted
def extract_code_and_response(text):
    match = re.search(r"## START CODE\s*(.*?)\s*## END CODE\s*(.*)", text, re.DOTALL)

    if match:
        code_block = match.group(1).strip()
        response_text = match.group(2).strip()

        # reformatting the tail_text
        response_text = response_text.replace("## RESPONSE","").replace("## END RESPONSE","")

        return code_block, response_text
    else:
        raise ValueError("Code block not found between '## START CODE' and '## END CODE'")

