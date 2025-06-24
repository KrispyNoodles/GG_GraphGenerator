from langchain.schema import HumanMessage, AIMessage
import re
from config import llm
from prompts import get_graph_prompt

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

