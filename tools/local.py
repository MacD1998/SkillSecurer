import os
from langchain_core.tools import tool

@tool
def read_local_file(path: str) -> str:
    """Reads the content of a local SKILL.md file."""
    try:
        with open(os.path.expanduser(path), errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return f"ERROR: file not found: {path}"
    except Exception as e:
        return f"ERROR: {e}"
