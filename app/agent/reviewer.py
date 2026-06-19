from langchain_core.messages import HumanMessage
from app.agent.state import AgentState
from app.agent.llm_utils import as_text, make_llm

llm = make_llm()

def _issue_context(messages):
    for msg in messages:
        if hasattr(msg, "name") and msg.name == "get_github_issue":
            return msg.content
    return "No issue found in context."

def reviewer_node(state: AgentState):
    """
        LLM review: does the patched code logically resolve the issue?
    """

    issue = _issue_context(state.get("messages", []))
    patched = state.get("patched_code", "")
    final_fix = state.get("final_fix", "")

    prompt = HumanMessage(
        content=(
            "You are a meticulous Senior Code Reviewer. A patch has passed syntax checks. "
            "Decide whether it CORRECTLY and COMPLETELY resolves the issue. Judge logic, not style.\n\n"
            f"--- GITHUB ISSUE ---\n{issue}\n\n"
            f"--- PATCH (SEARCH/REPLACE) ---\n{final_fix}\n\n"
            f"--- FULL PATCHED FILE ---\n{patched}\n\n"
            "If the fix is logically correct and resolves the issue, output EXACTLY: APPROVED\n"
            "If it is wrong, incomplete, or introduces a regression, output EXACTLY: "
            "REJECTED: <one concise, actionable reason>\n"
            "Output nothing else."
        )
    )
    resp = as_text(llm.invoke([prompt]).content).strip()

    if resp.upper().startswith("APPROVED"):
        return {"reviewer_feedback": ""} #empty feedback means pass
    
    reason = resp.split(":", 1)[1].strip() if ":" in resp else resp #non-empty means fail
    return {
        "reviewer_feedback": reason or "Reviewer rejected the patch.",
        "logic_attempts": state.get("logic_attempts", 0) + 1,
    }