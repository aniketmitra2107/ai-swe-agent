import os
import json
import uuid
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from app.agent.state import AgentState
from app.agent.tools import get_github_issue, get_file_content
from app.agent.list_directory import list_github_directory

load_dotenv()


llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0,
    num_ctx=16384
)

planner_llm = llm.bind_tools([get_github_issue, get_file_content, list_github_directory])

def planner_node(state: AgentState):
    """Analyzes the request and calls tools to fetch the issue and code context"""
    messages = state.get("messages",[])
    system_prompt = SystemMessage(
        content=(
            "You are an autonomous machine. You DO NOT converse. You NEVER summarize, echo, or repeat tool outputs back to the user.\n"
            "Evaluate your current context and take exactly ONE of the following actions:\n\n"
            "- IF you have not read the issue yet -> Call get_github_issue.\n"
            "- IF you have the issue, but haven't explored the repository -> Call list_github_directory.\n"
            "- IF you have explored the directory and know the exact source code file path -> Call get_file_content.\n"
            "- IF you have fetched BOTH the issue AND the source code file -> Output EXACTLY AND ONLY: 'Context successfully gathered. Passing to coder.'\n\n"
            "CRITICAL RULES:\n"
            "- Output ONLY a JSON tool call or the exact exit phrase. Do not write XML or markdown.\n"
            "- DO NOT attempt to read binary, image, or compiled files (e.g., .pkl, .png, .jpg, .pyc). Focus only on readable source code."
        )
    )
    
    response = planner_llm.invoke([system_prompt] + messages)


    content_str = response.content.strip()
    if not getattr(response, "tool_calls", None):
        if content_str.startswith("{") and '"name"' in content_str and '"arguments"' in content_str:
            try:
                
                tool_data = json.loads(content_str)
                
                
                response.tool_calls = [{
                    "name": tool_data["name"],
                    "args": tool_data["arguments"],
                    "id": f"call_{uuid.uuid4().hex[:8]}"
                }]
                
                
                response.content = ""                
            except json.JSONDecodeError:
                pass 

    return {"messages": [response]}

def coder_node(state: AgentState):
    """Reads the gathered context and generates the actual code fix"""
    messages = state.get("messages",[])
    issue_context = "No issue found in context."
    file_context = "No file found in context."

    for msg in messages:
        if hasattr(msg, "name"):
            if msg.name == "get_github_issue":
                issue_context = msg.content
            elif msg.name == "get_file_content":
                file_context = msg.content

    if file_context == "No file found in context.":
        return {"final_fix": "Agent failed to locate the necessary file within the tool limit. No patch generated."}


    system_prompt = SystemMessage(
        content=(
            "You are an expert, language-agnostic Senior Software Engineer. You do not explain yourself.\n"
        "Review the issue below, then determine the exact lines of code that need to be changed to fix the bug.\n\n"
        f"--- GITHUB ISSUE ---\n{issue_context}\n\n"
        f"--- SOURCE CODE ---\n{file_context}\n\n"
        "CRITICAL INSTRUCTION:\n"
        "Do NOT rewrite the entire file. You must output a SEARCH/REPLACE block containing only the changed lines.\n"
        "Format your response EXACTLY like this:\n"
        "```\n"
        "<<<<\n"
        "    // original code as it currently exists\n"
        "====\n"
        "    // your new fixed code\n"
        ">>>>\n"
        "```\n"
        "Only output the markdown block. Include a few unchanged context lines in the <<<< section so the exact location is clear."
        )
    )
    response = llm.invoke([system_prompt])
    return {
        "final_fix": response.content
    }
        