import sys
import os
from langchain_core.messages import HumanMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.nodes import planner_node, coder_node

def run_node_test():
    print("---Testing Planner Node Execution---")

    mock_state = {
        "messages": [
            HumanMessage(content="Look up issue 7443 in the repo psf/requests to see what needs fixing.")
        ],
        "issue_description": "",
        "fetched_code": "",
        "final_fix": ""
    }
    try:
        output_state = planner_node(mock_state)
        
        returned_messages = output_state.get("messages", [])
        if not returned_messages:
            print("No messages returned from planner_node.")
            return
        
        ai_message = returned_messages[0]
        print(f"Node execution successful.\n")
        print(f"AI Message Type: {type(ai_message).__name__}")

        if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
            print("Gemini successfully mapped the request to a tool call:")
            for tool_call in ai_message.tool_calls:
                print(f"   Tool Name: {tool_call['name']}")
                print(f"   Arguments: {tool_call['args']}\n")
        
        else:
            print("The model responded with text instead of a tool call.")
            print(f"Response content:\n{ai_message.content}\n")

    except Exception as e:
        print(f"Error during planner_node test: {str(e)}")


def run_coder_test():
    print("---Testing Code node execution---")
    mock_state = {
        "messages": [
            HumanMessage(content = "Fix the bug where the calculator subtracts instead of adds."),
            HumanMessage(content=(
                "Issue Description: The add function is broken.\n"
                "File Content (calculator.py):\n"
                "def add(a, b):\n"
                "    return a - b\n"
            ))
        ],
        "issue_description": "",
        "fetched_code": "",
        "final_fix": ""
    }
    try:
        output_state = coder_node(mock_state)
        final_fix = output_state.get("final_fix", "")
        if final_fix:
            print("Code node execution successful. Final fix generated:")
            print(final_fix)
        else:
            print("No final fix returned from coder_node.")
    except Exception as e:
        print(f"Error during coder_node test: {str(e)}")





if __name__ == "__main__":
    run_node_test()
    run_coder_test()