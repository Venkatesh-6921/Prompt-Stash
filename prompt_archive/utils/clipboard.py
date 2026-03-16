"""
Clipboard utilities — pyperclip wrapper with graceful fallback.
"""
from __future__ import annotations


def copy_to_clipboard(text: str) -> bool:
    """Copy *text* to the system clipboard. Returns True on success."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def read_from_clipboard() -> str:
    """Read text from the system clipboard. Returns empty string on failure."""
    try:
        import pyperclip
        return pyperclip.paste() or ""
    except Exception:
        return ""
