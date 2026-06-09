import os
from github import Github
from langchain_core.tools import tool

@tool
def list_github_directory(repo_name: str, directory_path: str = "") -> str:
    """Lists the contents of a directory in a GitHub repository. If the path points to a file, it returns an error message.
    """
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    gh = Github(token) if token else Github()

    try:
        repo = gh.get_repo(repo_name)
        contents = repo.get_contents(directory_path)

        if not isinstance(contents, list):
            return f"The path '{directory_path}' points to a file, not a directory."
        
        items = []
        for content in contents:
            item_type = "DIR" if content.type == "dir" else "FILE"
            items.append(f"[{item_type}] {content.path}")
        return "\n".join(items)
    
    except Exception as e:
        return f"Error occurred while listing directory contents: {str(e)}"