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

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

# Document Intelligence
ADI_KEY=config.get("ADI_KEY")
ADI_ENDPOINT=config.get("ADI_ENDPOINT")

# Azure Document Intelligence
document_intelligence_client  = DocumentIntelligenceClient(
    endpoint=ADI_ENDPOINT, credential=AzureKeyCredential(ADI_KEY)
)