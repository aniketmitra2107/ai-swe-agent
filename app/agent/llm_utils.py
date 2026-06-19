import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "moonshotai/kimi-k2.7-code")
OPENROUTER_MAX_TOKENS = int(os.environ.get("OPENROUTER_MAX_TOKENS", "4096"))


def make_llm(**kwargs):
    """Construct the shared LLM client (OpenRouter via the OpenAI-compatible API)."""
    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        temperature=0,
        max_tokens=OPENROUTER_MAX_TOKENS,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        **kwargs,
    )


def as_text(content):
    """Normalize a LangChain message `.content` into a plain string.

    OpenAI-compatible providers return a str, but some (and Gemini) return a
    list of content parts (strings or {"type": "text", "text": ...} dicts),
    which breaks any code that calls .strip() / treats it as a string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for part in content:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, dict):
                out.append(part.get("text", ""))
        return "".join(out)
    return str(content)
