import re

_BLOCK_RE = re.compile(r"<{4,}\s*\n?(.*?)\n?={4,}\s*\n?(.*?)\n?>{4,}", re.DOTALL)


def _apply_one(text: str, search: str, replace: str):
    """Apply a single SEARCH/REPLACE pair to `text`. Returns (result, "") or (None, reason)."""
    if search.strip() == "":
        return None, "Malformed patch: a SEARCH (<<<<) section is empty."

    if search in text:
        return text.replace(search, replace, 1), ""

    orig_lines = text.splitlines()
    search_lines = search.strip("\n").splitlines()
    replace_lines = replace.strip("\n").splitlines()

    s_norm = [ln.strip() for ln in search_lines]
    n = len(s_norm)

    if n:
        for i in range(len(orig_lines) - n + 1):
            window = [orig_lines[i + j].strip() for j in range(n)]
            if window == s_norm:
                matched_first = orig_lines[i]
                orig_indent = matched_first[: len(matched_first) - len(matched_first.lstrip())]
                search_first = search_lines[0]
                search_indent = search_first[: len(search_first) - len(search_first.lstrip())]

                reindented = []
                for ln in replace_lines:
                    if ln.startswith(search_indent):
                        reindented.append(orig_indent + ln[len(search_indent):])
                    else:
                        reindented.append(ln)

                patched_lines = orig_lines[:i] + reindented + orig_lines[i + n:]
                return "\n".join(patched_lines), ""

    return None, (
        "Patch did not apply: a SEARCH section was not found in the file. "
        "Copy the original lines into the <<<< section (indentation is tolerated, "
        "but the actual code tokens must match)."
    )


def apply_search_replace(original: str, patch_block: str):
    """
        Parses one OR MORE Aider-style <<<<  ====  >>>> blocks and applies them
        to `original`, in order, each against the running result.

        Returns (patched_code, "") on success or (None, reason) on failure.
        The failure reason is surfaced to the coder as verifier feedback.
    """

    if not patch_block:
        return None, "Empty patch: the coder produced no SEARCH/REPLACE block."

    text = patch_block.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()

    blocks = list(_BLOCK_RE.finditer(text))
    if not blocks:
        return None, (
            "Malformed patch: could not find a <<<<  ====  >>>> block. "
            "Output the original code, then ====, then the fixed code, closed with >>>>."
        )

    patched = original
    for idx, m in enumerate(blocks, 1):
        result, reason = _apply_one(patched, m.group(1), m.group(2))
        if result is None:
            return None, f"Block {idx} of {len(blocks)} failed: {reason}"
        patched = result

    return patched, ""
