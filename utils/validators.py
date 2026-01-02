"""
Z.M.ai - Validation Utilities

Provides input validation and sanitization functions.
"""

import re
import logging
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_api_key(api_key: str) -> bool:
    """
    Validate that an API key is present and looks reasonable.

    Args:
        api_key: The API key to validate

    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False

    # Basic check: should be at least 20 characters
    if len(api_key) < 20:
        logger.warning("API key seems too short")
        return False

    return True


def validate_query(query: str) -> tuple[bool, Optional[str]]:
    """
    Validate a user query.

    Args:
        query: The user query to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query:
        return False, "Query cannot be empty"

    query = query.strip()

    if len(query) < 3:
        return False, "Query is too short (minimum 3 characters)"

    if len(query) > 2000:
        return False, "Query is too long (maximum 2000 characters)"

    # Check for obviously malicious patterns
    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            logger.warning(f"Potentially malicious query detected: {query[:50]}...")
            return False, "Query contains invalid content"

    return True, None


def sanitize_query(query: str) -> str:
    """
    Sanitize a user query by removing potentially harmful content.

    Args:
        query: The query to sanitize

    Returns:
        Sanitized query
    """
    # Remove null bytes
    query = query.replace("\x00", "")

    # Normalize whitespace
    query = " ".join(query.split())

    return query.strip()


def validate_file_path(file_path: str | Path, must_exist: bool = True) -> tuple[bool, Optional[str]]:
    """
    Validate a file path.

    Args:
        file_path: The file path to validate
        must_exist: Whether the file must exist

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)

    if must_exist and not path.exists():
        return False, f"File does not exist: {file_path}"

    if path.exists() and not path.is_file():
        return False, f"Path is not a file: {file_path}"

    return True, None


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate a URL.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"

    # Basic URL pattern
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        return False, f"Invalid URL format: {url}"

    return True, None


def validate_chunk_size(size: int) -> tuple[bool, Optional[str]]:
    """
    Validate chunk size configuration.

    Args:
        size: Chunk size in characters

    Returns:
        Tuple of (is_valid, error_message)
    """
    if size < 100:
        return False, "Chunk size must be at least 100 characters"

    if size > 10000:
        return False, "Chunk size cannot exceed 10000 characters"

    return True, None


def validate_similarity_threshold(threshold: float) -> tuple[bool, Optional[str]]:
    """
    Validate similarity threshold.

    Args:
        threshold: Similarity threshold (0-1)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not (0.0 <= threshold <= 1.0):
        return False, "Similarity threshold must be between 0.0 and 1.0"

    return True, None


def validate_model_name(model: str) -> tuple[bool, Optional[str]]:
    """
    Validate Groq model name.

    Args:
        model: Model name

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_models = [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
    ]

    if model not in valid_models:
        return False, f"Invalid model name. Valid options: {', '.join(valid_models)}"

    return True, None


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def validate_config(config) -> List[str]:
    """
    Validate configuration object.

    Args:
        config: Configuration object to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Validate API key
    if hasattr(config, "groq") and hasattr(config.groq, "api_key"):
        if not validate_api_key(config.groq.api_key):
            errors.append("Groq API key is invalid or missing")

    # Validate RAG settings
    if hasattr(config, "rag"):
        if hasattr(config.rag, "chunk_size"):
            valid, err = validate_chunk_size(config.rag.chunk_size)
            if not valid:
                errors.append(f"Chunk size: {err}")

        if hasattr(config.rag, "similarity_threshold"):
            valid, err = validate_similarity_threshold(config.rag.similarity_threshold)
            if not valid:
                errors.append(f"Similarity threshold: {err}")

    return errors
