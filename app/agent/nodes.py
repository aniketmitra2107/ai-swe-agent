import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from app.agent.state import AgentState
from app.agent.tools import get_github_issue, get_file_content

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    api_key=gemini_api_key
)

planner_llm = llm.bind_tools([get_github_issue, get_file_content])

def planner_node(state: AgentState):
    """Analyzes the request and calls tools to fetch the issue and code context"""
    messages = state.get("messages",[])
    system_prompt = SystemMessage(
        content=(
            "You are an AI software architect. Use you tools to fetch the specified Github issue."
            "Based on the issue description, determine which file needs to be modified and fetch its content. "
            "Do not write the final code fix. Your only job is to gather the necessary context into the conversation history. "
        )
    )
    response = planner_llm.invoke([system_prompt]+messages)
    return {"messages": [response]}

def coder_node(state: AgentState):
    """Reads the gathered context and generates the actual code fix"""
    messages = state.get("messages",[])
    system_prompt = SystemMessage(
        content=(
            "You are an expert Python backend developer. Review the Github issue and the fetched code"
            "provided in the conversation history. Write the exact code fix required to resolve the issue. Only provide the code, no explanations."
            "Output only the patched code, do not repeat the entire file. Do not include any text other than the code itself."
        )
    )
    response = llm.invoke([system_prompt]+messages)
    return {
        "messages": [response],
        "final_fix": response.content
    }
        