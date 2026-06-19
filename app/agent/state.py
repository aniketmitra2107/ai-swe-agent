from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

    issue_description: str
    fetched_code: str
    final_fix: str

    repo_name: str
    file_path: str

    patched_code: str

    verifier_feedback: str
    reviewer_feedback: str

    syntax_attempts: int
    logic_attempts: int
    coder_calls: int
    
    pr_url: str
    status: str #pr_created|failed_syntax|failed_logic|failed_pr|aborted