import os
import json
from langchain_core.messages import HumanMessage
from app.agent.state import AgentState
from app.agent.patcher import apply_search_replace
from app.agent.llm_utils import as_text, make_llm

llm = make_llm()

_DETERMINISTIC = {".py", ".json"}
_LLM_FALLBACK = {".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".rb", ".rs", ".c", ".cpp", ".cs", ".php"}

def _deterministic_check(code: str, file_path: str):
    """
        Returns (ok, reason). Only called for extensions in _DETERMINISTIC.
    """
    _, ext = os.path.splitext(file_path.lower())
    try:
        if ext == ".py":
            compile(code, file_path, "exec")
        elif ext == ".json":
            json.loads(code)
        return True, ""
    except SyntaxError as e:
        return False, f"Python SyntaxError at line {e.lineno}: {e.msg}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e.msg} at line {e.lineno} col {e.colno}"
    except Exception as e:
        return False, f"Syntax check failed: {e}"
    

def _llm_check(code: str, file_path: str):
    """
        LLM fallback syntax check, Returns (ok, reason).
    """
    prompt = HumanMessage(
        content=(
            "You are strict syntax linter. Examine the following source file for SYNTAX "
            "errors ONLY (do not judge logic, style, or correctness).\n"
            f"---FILE: {file_path} ---\n{code}\n---END---\n\n"
            "If the syntax is valid, output EXACTLY: VALID\n"
            "If there is a syntax error, output EXACTLY: INVALID: <one-line reason>\n"
            "Output nothing else."
        )
    )
    resp = as_text(llm.invoke([prompt]).content).strip()
    if resp.upper().startswith("VALID"):
        return True, ""
    reason = resp.split(":", 1)[1].strip() if ":" in resp else resp
    return False, reason or "LLM flagged a syntax error."

def verifier_node(state: AgentState):
    """
        Applies the patch in memory and checks for syntax errors.
    """
    final_fix = state.get("final_fix", "")
    original = state.get("fetched_code", "")
    file_path = state.get("file_path", "")

    patched, reason = apply_search_replace(original, final_fix)
    if patched is None:
        print("\n--- PATCH FAILED TO APPLY ---")
        print("Reason:", reason)
        print("--- MODEL'S RAW PATCH (first 800 chars) ---")
        print(final_fix[:800])
        print("--- END PATCH ---\n")
        return {
            "verifier_feedback": reason,
            "syntax_attempts": state.get("syntax_attempts", 0) + 1,
        }
    
    _, ext = os.path.splitext(file_path.lower())
    if ext in _DETERMINISTIC:
        ok, reason = _deterministic_check(patched, file_path)
    elif ext in _LLM_FALLBACK:
        ok, reason = _llm_check(patched, file_path)
    else:
        ok, reason = True, ""


    if not ok:
        return {
            "verifier_feedback": reason,
            "syntax_attempts": state.get("syntax_attempts", 0) + 1
        }
    
    return {
        "patched_code": patched,
        "verifier_feedback": "",
    }