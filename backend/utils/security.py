"""
Security utilities for Supply Chain Orchestrator AI System.
Input sanitization, prompt injection prevention, external data validation.
"""

from __future__ import annotations

import html
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Patterns that could indicate prompt injection attempts
_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"ignore\s+all\s+instructions",
    r"forget\s+(everything|all|prior)",
    r"you\s+are\s+now",
    r"new\s+instructions:",
    r"system\s+prompt",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<SYS>>",
    r"</s>",
    r"JAILBREAK",
]

_INJECTION_REGEX = re.compile(
    "|".join(_INJECTION_PATTERNS),
    re.IGNORECASE | re.DOTALL,
)


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitizes user or external input strings.
    - Strips HTML entities
    - Removes prompt injection patterns
    - Truncates to max_length
    - Strips leading/trailing whitespace
    """
    if not isinstance(text, str):
        text = str(text)

    # HTML escape
    text = html.unescape(text)

    # Detect and strip injection attempts
    if _INJECTION_REGEX.search(text):
        logger.warning("Potential prompt injection detected and sanitized")
        text = _INJECTION_REGEX.sub("[REDACTED]", text)

    # Remove null bytes and control chars (except common whitespace)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text[:max_length].strip()


def validate_external_data(data: Any) -> None:
    """
    Basic validation of external API responses.
    Raises ValueError if data looks malicious or malformed.
    """
    if data is None:
        raise ValueError("External data response is None")

    if isinstance(data, dict):
        # Check for unexpected script injection in values
        serialized = str(data)
        if _INJECTION_REGEX.search(serialized):
            logger.warning("Suspicious content detected in external API response")
            raise ValueError("External data contains suspicious content")

    if isinstance(data, list) and len(data) == 0:
        return  # Empty list is valid


def validate_tool_access(tool_name: str, allowed_tools: list[str]) -> None:
    """
    Validates that a tool is in the allowed list before execution.
    Raises PermissionError if not allowed.
    """
    if tool_name not in allowed_tools:
        logger.error(f"Unauthorized tool access attempt: {tool_name}")
        raise PermissionError(f"Tool '{tool_name}' is not in the allowed tool list")
