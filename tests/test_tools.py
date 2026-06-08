import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.tools import get_github_issue, get_file_content

def run_tests():
    print("Testing get_github_issue...")
    try:
        issue_response = get_github_issue.invoke({
            "repo_name": "psf/requests",
            "issue_number": 7443
        })
        print(f"Result:\n{issue_response[:300]}...\n")
    except Exception as e:
        print(f"Error during get_github_issue test: {str(e)}")

    print("Testing get_file_content...")
    try:
        file_response = get_file_content.invoke({
            "repo_name": "psf/requests",
            "file_path": "requests/__init__.py"
        })
        print(f"Result:\n{file_response[:300]}...\n")
    except Exception as e:
        print(f"Error during get_file_content test: {str(e)}")

if __name__ == "__main__":
    run_tests()