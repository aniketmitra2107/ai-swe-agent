import sys
import os
from langchain_core.messages import HumanMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.agent.graph import agent_app

def run_full_graph():
    print("---Testing Full Graph Execution---")

    intital_state = {
        "messages": [
            HumanMessage(content=
                "Look up issue 1 in the repo aniketmitra2107/ai-swe-agent. "
                "You must use the list_github_directory tool to explore the folder structure and find the correct file. "
                "Once you find it, fetch its content. DO NOT write any code or patches."
            )
        ],
        "issue_description": "",
        "fetched_code": "",
        "final_fix": "",
        "repo_name": "",
        "file_path": "",
        "patched_code": "",
        "verifier_feedback": "",
        "reviewer_feedback": "",
        "syntax_attempts": 0,
        "logic_attempts": 0,
        "coder_calls": 0,
        "pr_url": "",
        "status": "",
    }

    try:
        for output in agent_app.stream(intital_state):
            for node_name, state_update in output.items():
                print(f"\nFinished Node: {node_name}")
                
                if node_name == "coder":
                    print("\n--- FINAL CODE FIX---")
                    print(state_update.get("final_fix"))
                
                if node_name == "tools":
                    messages = state_update.get("messages", [])
                    if messages and hasattr(messages[-1], 'content'):
                        tool_result = messages[-1].content
                        print(f"Tool Result Preview: {tool_result[:200]}...")
                        if "Error" in tool_result or "404" in tool_result:
                            print("WARNING: Tool returned an error! This is why the planner is looping.")

                if node_name == "verifier":
                    print("Verifier feedback:", state_update.get("verifier_feedback") or "PASS")

                if node_name == "reviewer":
                    print("Reviewer feedback:", state_update.get("reviewer_feedback") or "APPROVED")

                if node_name in ("pr", "fail_syntax", "fail_logic"):
                    print("STATUS:", state_update.get("status"), "| PR:", state_update.get("pr_url", ""))
                    if state_update.get("status") == "failed_pr":
                        print("PR ERROR:", state_update.get("verifier_feedback"))

    except Exception as e:
        print(f"Error during full graph execution: {str(e)}")
    
if __name__ == "__main__":
    run_full_graph()