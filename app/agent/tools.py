import os
import base64
from github import Github
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

github_token = os.getenv("GITHUB_ACCESS_TOKEN")
if not github_token:
    raise ValueError("GITHUB_ACCESS_TOKEN is not set in the environment variables.")    

gh = Github(github_token)

@tool
def get_github_issue(repo_name: str, issue_number: int) -> str:
    """Fetches the title and body of a GitHub issue given the repository name and issue number."""
    try:
        repo = gh.get_repo(repo_name)
        issue = repo.get_issue(number=issue_number)
        labels = [label.name.lower() for label in issue.labels]

        if "bug" not in labels:
            return (
                f"SCOPE EXCEPTION: Issue #{issue_number} is tagged as {labels}. "
                f"It is NOT tagged as a 'bug'. You are restricted to bug fixes only. "
                f"Do NOT call any more tools. Output exactly: 'Out of scope: Not a bug. Aborting.'"
            )
        content = f"Issue Title: {issue.title}\n"
        content += f"labels: {labels}\n"
        content += f"Issue Body: {issue.body}"
        return content
         
    except Exception as e:
        return f"Error fetching issue: {str(e)}"
    
@tool
def get_file_content(repo_name: str, file_path: str) -> str:
    """Fetches the content of a file given the repository name and file path."""
    try:
        repo = gh.get_repo(repo_name)
        file_content = repo.get_contents(file_path)

        try:
            return file_content.decoded_content.decode("utf-8")
        except UnicodeDecodeError:
            return (
                f"Error: '{file_path}' appears to be a binary/compiled file "
                f"(like .pkl, .png, .exe). You cannot read this file. "
                f"Please explore other directories for readable source code."
            )
            
    except Exception as e:
        return f"Error fetching file content: {str(e)}"