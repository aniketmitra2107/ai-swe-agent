import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-pro",
    temperature=0,
    api_key=gemini_api_key
)