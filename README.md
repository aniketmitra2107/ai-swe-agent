#  🤖 Local AI Software Engineer (SWE) Agent

  

An autonomous, local-first AI software engineering agent built with **LangGraph** and **Ollama**. This agent can navigate a real-world GitHub repository, locate the source of a bug, write a surgical code patch, and automatically open a Pull Request—all powered by a local 7B LLM (Qwen 2.5 Coder).

  

##  ✨ Features

  

-  **Local-First & Private:** Uses Ollama to run the LLM locally. No code is sent to OpenAI or Anthropic.

-  **ReAct Orchestration:** Powered by a LangGraph state machine that acts, observes, and reasons through a repository.

-  **Smart Directory Traversal:** Navigates deeply nested repository structures using custom PyGithub tools.

-  **Fail-Fast Scope Bouncer:** Automatically rejects feature requests or enhancements, restricting execution exclusively to issues tagged with `bug` to save tokens and prevent hallucinations.

-  **"Clean Plate" Handoff:** Prevents context-window crashes by stripping out intermediate tool noise before handing the final context to the Coder node.

-  **Surgical Patching:** Uses the Aider-style `<<<< ==== >>>>` Search/Replace block format instead of rewriting entire files.

-  **Automated Pull Requests:** Branches the repository, applies the patch in memory, and opens a GitHub PR automatically.

-  **Fully Dockerized:** Runs in an isolated container to ensure environment consistency.

  

---

  

##  🏗️ Architecture

  

The agent operates on a directed graph built with LangGraph:

  

1.  **Planner Node:** The "eyes" of the agent. It uses native tool calling to fetch the GitHub issue, traverse directories, and read file contents.

2.  **Router (Circuit Breaker):** Ensures the Planner is actually calling tools. It cuts off the loop if the agent gets stuck or exceeds its "stamina" (15 tool calls).

3.  **Coder Node:** The "hands" of the agent. It receives a clean prompt containing *only* the issue and the exact file content, outputting a precise patch.

4.  **PR Node:** The Git orchestrator. It parses the patch, clones the target repo, applies the fix, commits to a new branch, and opens a Pull Request.

  

---

  

##  📋 Prerequisites

  

Before running the agent, you need to set up your local environment:

  

1.  **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** installed and running.

2.  **[Ollama](https://ollama.com/)** installed and running on your host machine.

3.  **Download the Model:** Open your terminal and pull the Qwen Coder model:

```shell
ollama run qwen2.5-coder:7b
```

  
GitHub Personal Access Token (PAT): You need a classic PAT with repo (Read/Write) access to fetch issues and open Pull Requests.

  

🚀 Quick Start (Docker)

The easiest and safest way to run the agent is using Docker Compose.

  

1. Clone the repository:

  

```shell
git clone [https://github.com/aniketmitra2107/ai-swe-agent.git](https://github.com/aniketmitra2107/ai-swe-agent.git)
cd ai-swe-agent
```

  

2. Set your GitHub Token:

Export your token to your terminal environment so Docker can securely pass it into the container.

Windows (PowerShell): `$env:GITHUB_TOKEN="ghp_your_token_here"`
Mac/Linux: `export GITHUB_TOKEN="ghp_your_token_here"`

  

3. Run the Agent:

```shell
docker-compose up --build
```

  

The agent will spin up, connect to your local Ollama instance, and begin executing the test graph. Watch the terminal logs as it traverses the repository and opens the PR!

  

💻 Local Setup (Without Docker)

If you prefer to run the agent directly on your host machine for debugging:

  

1. Create a virtual environment:

  
```shell
python -m venv venv
source venv/bin/activate # On Windows use: .\venv\Scripts\activate
```
  

2. Install dependencies:

  
```shell
pip install -r requirements.txt
```
  

3. Set environment variables:
```shell
export GITHUB_ACCESS_TOKEN="ghp_your_token_here"
```
  

4. Execute the test script:

  
```shell
python tests/test_graph.py
```
  
  

🧠 Customizing the Agent

To test the agent against a different repository or bug:

  

1. Open `tests/test_graph.py`

2. Update the initial message payload with the target repository and issue number:

  
```shell
initial_state = {
    "messages": [
        HumanMessage(content="Fix bug in repository 'your-username/your-repo' for issue #123.")
    ]
}
```
  

Note: Make sure the repository actually has an issue with the label bug, otherwise the agent's Scope Bouncer will immediately abort the execution.

  

⚠️ Limitations & Future Work

- Hardware Limits: A 16k context window is required for reading large files. Ensure you have sufficient RAM/VRAM to run 7B parameter models locally. If CUDA crashes, lower num_ctx in nodes.py.
 
- Single-File Bias: Currently, the agent is optimized to find and patch a single file per execution.
 
- Execution Verification: Future iterations will include a Verifier Node that runs the repository's test suite (pytest, npm test) inside an isolated ephemeral container before opening a PR.

  

📜 License

This project is licensed under the MIT License.