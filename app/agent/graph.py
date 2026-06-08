from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.agent.state import AgentState
from app.agent.nodes import planner_node, coder_node
from app.agent.tools import get_github_issue, get_file_content

tools = [get_github_issue, get_file_content]
tool_node = ToolNode(tools)

def router(state: AgentState):
    """
    Checks the last message from the planner. If it contains tool calls, route to the tools.
    If not, it means the planner has already provided the necessary context and we can move to the coder node.
    """

    messages = state.get("messages", [])
    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "coder"

workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("tools", tool_node)
workflow.add_node("coder", coder_node)

#define the flow of the graph
workflow.set_entry_point("planner")

#from the planner we consult the router to see where to go next
workflow.add_conditional_edges(
    "planner",
    router,
    {
        "tools": "tools",
        "coder": "coder"
    }
)
#after tools execute, loop back to the planner to see if we need to fetch more context or if we have everything we need to generate the fix
workflow.add_edge("tools", "planner")
#once the coder node executes, we are done and can end the workflow
workflow.add_edge("coder", END)
#compile the graph into an executable agent application
agent_app = workflow.compile()