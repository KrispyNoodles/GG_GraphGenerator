from langchain_openai import AzureChatOpenAI
from dotenv import dotenv_values

config = dotenv_values(".env")

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

API_MINI_KEY=config.get("API_MINI_KEY")
API_MINI_ENDPOINT=config.get("API_MINI_ENDPOINT")
API_MINI_MODEL=config.get("API_MINI_MODEL")

# Initialize the 4o mini LLM
llm_mini = AzureChatOpenAI(
                model=API_MINI_MODEL, 
                openai_api_version="2024-12-01-preview",
                api_key= API_MINI_KEY,
                azure_endpoint=API_MINI_ENDPOINT
                )