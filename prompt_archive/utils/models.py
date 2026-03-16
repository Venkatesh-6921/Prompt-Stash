"""
Known AI model name registry.
Used for validation and display normalisation.
"""
from __future__ import annotations

KNOWN_MODELS: dict[str, list[str]] = {
    "claude":   ["claude", "claude-3", "claude-3.5", "claude-opus", "claude-sonnet", "claude-haiku"],
    "gpt4o":    ["gpt4o", "gpt-4o", "gpt-4", "gpt4", "chatgpt"],
    "gemini":   ["gemini", "gemini-pro", "gemini-ultra", "gemini-flash"],
    "llama":    ["llama", "llama3", "llama-3"],
    "mistral":  ["mistral", "mixtral"],
    "deepseek": ["deepseek", "deepseek-v2", "deepseek-coder"],
}


def normalise_model(name: str) -> str:
    """Return the canonical model family name, or the original if unknown."""
    lower = name.strip().lower()
    for canonical, aliases in KNOWN_MODELS.items():
        if lower in aliases:
            return canonical
    return lower
