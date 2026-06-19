# 🤖 AI Software Engineer (SWE) Agent

An autonomous AI software engineering agent built with **LangGraph**. It navigates a real GitHub repository, locates the source of a bug, writes a surgical code patch, **verifies the patch is syntactically valid**, has a **reviewer confirm the fix is logically correct**, and only then opens a Pull Request.

LLM inference runs through **[OpenRouter](https://openrouter.ai/)** (an OpenAI-compatible API), so you can point the agent at any hosted model — DeepSeek, Qwen Coder, Kimi, Claude, GPT, etc. — by changing a single environment variable.

## ✨ Features

- **Model-Agnostic via OpenRouter:** Switch the underlying LLM with one env var (`OPENROUTER_MODEL`) — no code changes. The client is centralized in `app/agent/llm_utils.py`.
- **ReAct Orchestration:** A LangGraph state machine that acts, observes, and reasons through a repository.
- **Smart Directory Traversal:** Navigates deeply nested repository structures using custom PyGithub tools.
- **Fail-Fast Scope Bouncer:** Restricts execution to issues tagged `bug`, rejecting feature requests to save tokens and prevent hallucinations.
- **"Clean Plate" Handoff:** Strips intermediate tool noise before handing the final context to the Coder, preventing context-window bloat.
- **Surgical Patching:** Uses the Aider-style `<<<< ==== >>>>` SEARCH/REPLACE format instead of rewriting whole files. Supports multiple blocks per patch and tolerates whitespace/indentation drift.
- **Syntax Verifier:** Applies the patch in memory and checks it parses — deterministic `compile()` / `json.loads` for Python/JSON, with an LLM fallback for other languages. Broken syntax never reaches a PR.
- **Logical Reviewer:** A second LLM pass confirms the patch actually resolves the issue before a PR is opened.
- **Bounded Self-Correction:** Independent retry budgets for syntax fixes and logic rewrites, under a global ceiling — the Coder iterates on feedback without looping forever.
- **Automated Pull Requests:** Branches the repo, commits the patched file, and opens a PR. If the reviewer can't be satisfied within budget, it opens a **draft PR flagged for human review** with the reviewer's objection embedded.
- **Fully Dockerized:** Runs in an isolated container for environment consistency.

---

## 🏗️ Architecture

The agent operates on a directed graph built with LangGraph:

1. **Planner Node:** The "eyes" of the agent. Uses native tool calling to fetch the GitHub issue, traverse directories, and read file contents.
2. **Router (Circuit Breaker):** Ensures the Planner keeps making progress and cuts off the loop if it exceeds its tool "stamina" (15 tool calls).
3. **Coder Node:** The "hands" of the agent. Receives a clean prompt with *only* the issue and the exact file content, and outputs a precise SEARCH/REPLACE patch. Re-runs with feedback when a gate rejects its work.
4. **Verifier Node:** Applies the patch in memory and checks the result is syntactically valid.
5. **Reviewer Node:** Judges whether the patched code logically resolves the issue.
6. **PR Node:** The Git orchestrator. Branches the repo, commits the patched file, and opens a Pull Request (or a draft PR if the logic review was never satisfied).

```
Planner ─► Router ─► Tools ─┐
   ▲                        │
   └────────────────────────┘
Router ─► Coder ─► Verifier ─► Reviewer ─► PR ─► ✅ Pull Request
                     │            │
              syntax fail    logic reject
                     │            │
              retry Coder    retry Coder      (within budget)
                     │            │
              budget spent   budget spent
                     ▼            ▼
               fail_syntax   📝 Draft PR (flagged for human review)
```

**Retry budgets** (configured in `app/agent/graph.py`):

| Constant | Default | Meaning |
|---|---|---|
| `MAX_SYNTAX_FIXES` | 3 | Coder retries allowed for syntax failures |
| `MAX_LOGIC_FIXES` | 3 | Coder retries allowed for logic rejections |
| `MAX_CODER_CALLS` | 8 | Global ceiling on total Coder invocations |

---

## 📋 Prerequisites

1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** installed and running (for the containerized run).
2. **An [OpenRouter API key](https://openrouter.ai/keys)** — the agent calls models through OpenRouter.
3. **A GitHub Personal Access Token (PAT)** with `repo` (Read/Write) access, to fetch issues and open Pull Requests.

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```ini
OPENROUTER_API_KEY=sk-or-v1-your_key_here
GITHUB_ACCESS_TOKEN=ghp_your_token_here

# Optional — override the defaults in app/agent/llm_utils.py
OPENROUTER_MODEL=deepseek/deepseek-chat
OPENROUTER_MAX_TOKENS=4096
```

`.env` is git-ignored and excluded from the Docker image, so your secrets are never committed or baked into a build. Docker Compose injects these variables into the container via `env_file`.

> **Tip:** `OPENROUTER_MAX_TOKENS` caps output tokens. Keep it modest (e.g. `4096`) — without a cap, OpenRouter reserves the model's full completion length and may reject the request if your credit balance can't cover the worst case.

---

## 🚀 Quick Start (Docker)

1. **Clone the repository:**

   ```shell
   git clone https://github.com/aniketmitra2107/ai-swe-agent.git
   cd ai-swe-agent
   ```

2. **Create your `.env`** as described in [Configuration](#️-configuration).

3. **Run the agent:**

   ```shell
   docker compose up --build
   ```

The agent will spin up, connect to OpenRouter, traverse the target repository, and (on success) open a Pull Request. Watch the terminal logs to follow each node.

---

## 💻 Local Setup (Without Docker)

1. **Create a virtual environment:**

   ```shell
   python -m venv venv
   source venv/bin/activate   # On Windows: .\venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```shell
   pip install -r requirements.txt
   ```

3. **Provide credentials** via a `.env` file (see [Configuration](#️-configuration)) — it's loaded automatically.

4. **Execute the test script:**

   ```shell
   python tests/test_graph.py
   ```

---

## 🧠 Customizing the Agent

**Target a different repo/issue:** open `tests/test_graph.py` and edit the initial message payload:

```python
initial_state = {
    "messages": [
        HumanMessage(content="Look up issue 1 in the repo your-username/your-repo. ...")
    ],
    # ... remaining state fields
}
```

**Switch the LLM:** set `OPENROUTER_MODEL` in `.env` (e.g. `deepseek/deepseek-chat`, `qwen/qwen3-coder`, `anthropic/claude-sonnet-4-6`). Browse options on the [OpenRouter models page](https://openrouter.ai/models) — prefer models that advertise tool/function calling, since the Planner relies on it.

> **Note:** The target repository must have an issue labeled `bug`, or the Scope Bouncer will abort immediately.

---

## ⚠️ Limitations & Future Work

- **Single-File Bias:** The agent is currently optimized to locate and patch a single file per execution.
- **Syntax ≠ Behavior:** The Verifier confirms the patch *parses*, but does not run the repository's test suite. A future iteration will execute `pytest` / `npm test` inside an ephemeral container before opening a PR.
- **API Cost & Rate Limits:** Running through hosted models incurs per-token cost (and free tiers impose request limits). A full run makes ~8–10 model calls; choose your model and credit budget accordingly.

---

## 📜 License

This project is licensed under the MIT License.
