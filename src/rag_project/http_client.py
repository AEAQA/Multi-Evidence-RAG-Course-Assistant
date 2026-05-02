"""Tiny JSON HTTP helper for optional API clients."""

from __future__ import annotations

from typing import Any

import requests


def post_json(
    url: str,
    *,
    headers: dict[str, str],
    json: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    """POST JSON and return the parsed response body."""
    response = requests.post(url, headers=headers, json=json, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Expected JSON object response")
    return payload
