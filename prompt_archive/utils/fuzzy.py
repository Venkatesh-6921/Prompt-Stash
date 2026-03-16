"""
Fuzzy name matching using rapidfuzz.
"""
from __future__ import annotations


def fuzzy_find(query: str, names: list[str], threshold: int = 60) -> str | None:
    """Return the best fuzzy match for *query* among *names*, or None."""
    if not names:
        return None
    try:
        from rapidfuzz import process, fuzz
        result = process.extractOne(query, names, scorer=fuzz.WRatio, score_cutoff=threshold)
        return result[0] if result else None
    except ImportError:
        # Fallback: simple substring match
        for name in names:
            if query.lower() in name.lower():
                return name
        return None
