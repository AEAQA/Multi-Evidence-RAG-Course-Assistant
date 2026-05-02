"""Small deterministic tokenizer for retrieval baselines."""

from __future__ import annotations

import re

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric terms."""
    return TOKEN_PATTERN.findall(text.lower())
