from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from app.agent.state import AgentState
from app.agent.nodes import planner_node, coder_node
from app.agent.tools import get_github_issue, get_file_content
from app.agent.list_directory import list_github_directory

tools = [get_github_issue, get_file_content, list_github_directory]
tool_node = ToolNode(tools)


def router(state: AgentState):
    """
    Checks the last message from the planner. 
    Routes to tools if native calls exist, catches LLM formatting hallucinations, 
    and enforces a strict tool execution limit to prevent infinite loops.
    """
    messages = state.get("messages", [])
    last_message = messages[-1]

    tool_run_count = 0
    for m in messages:
        if isinstance(m, dict) and m.get("type") == "tool":
            tool_run_count += 1
        elif hasattr(m, "type") and m.type == "tool":
            tool_run_count += 1
            
    if tool_run_count >= 15:
        return "coder"

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    if isinstance(last_message, dict) and last_message.get("tool_calls"):
        return "tools"

    
    content = last_message.content if hasattr(last_message, "content") else last_message.get("content", "")
    
    
    if "Context successfully gathered" in content:
        return "coder"

    if "Out of scope" in content or "Aborting" in content:
        return END    
   
    return "coder"

workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("tools", tool_node)
workflow.add_node("coder", coder_node)

workflow.set_entry_point("planner")

workflow.add_conditional_edges(
    "planner",
    router,
    {
        "tools": "tools",
        "coder": "coder"
    }
)
workflow.add_edge("tools", "planner")
workflow.add_edge("coder", END)

agent_app = workflow.compile()