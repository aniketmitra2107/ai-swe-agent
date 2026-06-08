import os
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
        return f"Issue Title: {issue.title}\nIssue Body: {issue.body}"
    except Exception as e:
        return f"Error fetching issue: {str(e)}"
    
@tool
def get_file_content(repo_name: str, file_path: str) -> str:
    """Fetches the content of a file given the repository name and file path."""
    try:
        repo = gh.get_repo(repo_name)
        file_content = repo.get_contents(file_path)
        return file_content.decoded_content.decode("utf-8")
    except Exception as e:
        return f"Error fetching file content: {str(e)}"