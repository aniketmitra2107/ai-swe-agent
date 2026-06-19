from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from app.agent.state import AgentState
from app.agent.nodes import planner_node, coder_node
from app.agent.verifier import verifier_node
from app.agent.reviewer import reviewer_node
from app.agent.pr_node import pr_node
from app.agent.tools import get_github_issue, get_file_content
from app.agent.list_directory import list_github_directory

tools = [get_github_issue, get_file_content, list_github_directory]
tool_node = ToolNode(tools)

MAX_SYNTAX_FIXES = 3
MAX_LOGIC_FIXES = 3
MAX_CODER_CALLS = 8

def router(state: AgentState):
    """
        Planner circuit breaker (unchanged logic).
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

def verifier_router(state: AgentState):
    """Pass -> reviewer  Fail -> coder (if budget) else END."""
    if not state.get("verifier_feedback"):
        return "reviewer"
    if state.get("syntax_attempts", 0) < MAX_SYNTAX_FIXES and state.get("coder_calls", 0) < MAX_CODER_CALLS:
        return "coder"
    return "fail_syntax"

def reviewer_router(state: AgentState):
    """Approved -> PR  Rejected -> coder (if budget) else END."""

    if not state.get("reviewer_feedback"):
        return "pr"
    if state.get("logic_attempts", 0) < MAX_LOGIC_FIXES and state.get("coder_calls", 0) < MAX_CODER_CALLS:
        return "coder"
    return "pr"

def _fail_syntax(state: AgentState):
    return {
        "status": "failed_syntax"
    }

# def _fail_logic(state: AgentState):
#     return {
#         "status": "fail_logc"
#     }

workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("tools", tool_node)
workflow.add_node("coder", coder_node)
workflow.add_node("verifier", verifier_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("pr", pr_node)
workflow.add_node("fail_syntax", _fail_syntax)
#workflow.add_node("fail_logic", _fail_logic)

workflow.set_entry_point("planner")

workflow.add_conditional_edges(
    "planner",
    router,
    {"tools": "tools", "coder": "coder", END: END}
)

workflow.add_edge("tools", "planner")

#coder always hands off to the verifier node
workflow.add_edge("coder", "verifier")
workflow.add_conditional_edges(
    "verifier",
    verifier_router,
    {"reviewer": "reviewer", "coder": "coder", "fail_syntax": "fail_syntax"}
)

workflow.add_conditional_edges(
    "reviewer",
    reviewer_router,
    {"pr":"pr", "coder":"coder"}
)

workflow.add_edge("pr", END)
workflow.add_edge("fail_syntax", END)
#workflow.add_edge("fail_logic", END)

agent_app = workflow.compile()