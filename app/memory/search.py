"""Keyword relevance scoring for memory search."""

from __future__ import annotations


def score_memory_match(query: str, content: str, tags: list[str]) -> float:
    """Score how well a memory matches a search query.

    Args:
        query: User search query.
        content: Memory fact content.
        tags: Memory tags.

    Returns:
        Relevance score (0.0 when no match).
    """
    normalized_query = query.strip().lower()
    if not normalized_query:
        return 0.0

    haystack = " ".join([content.lower(), " ".join(tag.lower() for tag in tags)])
    tokens = [token for token in normalized_query.split() if token]
    if not tokens:
        return 0.0

    score = 0.0
    for token in tokens:
        if token in haystack:
            score += 1.0
        if token in content.lower():
            score += 0.5

    if normalized_query in content.lower():
        score += 2.0

    return score
