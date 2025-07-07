def table_name_gnereator_prompt(dataframe):

    # retrieving the first 3 rows only so as to not feed the entire csv into the gpt model
    csv_sample = dataframe.head(3).to_csv(index=False)

    return f"""
    You are a smart assistant. Based on the following CSV sample, generate a short, meaningful name for the table.

    Instructions:
    - Respond with only the name — no explanation, no punctuation, and no formatting.
    - You may use spaces and line breaks freely in your response where appropriate.
    - Preserve the format and indentation of any input text shown.

    CSV Sample:
    {csv_sample}

    Table name:"""

# getting the a mini LLM to read the data
from langchain_core.messages import AIMessage
from config import llm_mini

# function that generates a name
def name_generator(csv_file):
    
    main_prompt = table_name_gnereator_prompt(csv_file)
    main_prompt = AIMessage(content=main_prompt)

    response = llm_mini.invoke([main_prompt])

    return response.content