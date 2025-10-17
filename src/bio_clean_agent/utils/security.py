"""Security utilities for the Bio Clean Agent."""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from pathlib import Path
from typing import List, Optional, Set


# File upload security constants
ALLOWED_EXTENSIONS: Set[str] = {".csv", ".txt", ".xlsx", ".xls", ".tsv", ".json"}
MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
MAX_FILENAME_LENGTH: int = 255


class SecurityError(Exception):
    """Raised when a security validation fails."""


def validate_file_upload(
    filename: str,
    file_size: int,
    allowed_extensions: Optional[Set[str]] = None,
    max_size: Optional[int] = None,
) -> None:
    """
    Validate file upload security.

    Args:
        filename: Name of the uploaded file
        file_size: Size of the file in bytes
        allowed_extensions: Set of allowed file extensions (default: ALLOWED_EXTENSIONS)
        max_size: Maximum file size in bytes (default: MAX_FILE_SIZE)

    Raises:
        SecurityError: If validation fails
    """
    if not filename:
        raise SecurityError("Filename cannot be empty")

    # Check filename length
    if len(filename) > MAX_FILENAME_LENGTH:
        raise SecurityError(f"Filename too long (max {MAX_FILENAME_LENGTH} characters)")

    # Sanitize and validate filename
    safe_filename = sanitize_filename(filename)
    if safe_filename != filename:
        raise SecurityError(
            f"Filename contains invalid characters. Use only alphanumeric, dash, underscore, and dot."
        )

    # Check file extension
    extensions = allowed_extensions or ALLOWED_EXTENSIONS
    file_ext = Path(filename).suffix.lower()
    if file_ext not in extensions:
        raise SecurityError(
            f"File type not allowed. Allowed types: {', '.join(sorted(extensions))}"
        )

    # Check file size
    max_allowed = max_size or MAX_FILE_SIZE
    if file_size > max_allowed:
        raise SecurityError(
            f"File too large. Maximum size: {max_allowed / (1024*1024):.1f}MB"
        )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and injection attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem operations
    """
    # Remove path components
    filename = Path(filename).name

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Allow only safe characters: alphanumeric, dash, underscore, dot
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    # Prevent hidden files
    if filename.startswith("."):
        filename = "_" + filename[1:]

    # Prevent empty filename
    if not filename or filename == ".":
        filename = "unnamed_file"

    return filename


def generate_secure_id() -> str:
    """
    Generate a cryptographically secure random ID.

    Returns:
        32-character hexadecimal string
    """
    return secrets.token_hex(16)


def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """
    Mask sensitive values (e.g., API keys) for logging.

    Args:
        value: Sensitive value to mask
        show_chars: Number of characters to show at the end (default: 4)

    Returns:
        Masked string like "****abc123"
    """
    if not value or len(value) <= show_chars:
        return "*" * 8

    return "*" * 8 + value[-show_chars:]


def hash_phi_value(value: str, salt: Optional[str] = None) -> str:
    """
    Create a consistent hash for PHI values.

    Args:
        value: PHI value to hash
        salt: Optional salt for hashing (recommended for production)

    Returns:
        SHA-256 hash of the value
    """
    if salt:
        value = salt + value

    return hashlib.sha256(value.encode()).hexdigest()


def validate_path_traversal(path: Path, base_dir: Path) -> None:
    """
    Validate that a path doesn't escape the base directory.

    Args:
        path: Path to validate
        base_dir: Base directory that path should be contained within

    Raises:
        SecurityError: If path attempts directory traversal
    """
    try:
        # Resolve to absolute paths
        abs_path = path.resolve()
        abs_base = base_dir.resolve()

        # Check if path is within base directory
        if not str(abs_path).startswith(str(abs_base)):
            raise SecurityError(
                f"Path traversal attempt detected: {path} is outside {base_dir}"
            )
    except Exception as e:
        raise SecurityError(f"Invalid path: {e}")


def get_allowed_origins() -> List[str]:
    """
    Get allowed CORS origins from environment or use secure defaults.

    Returns:
        List of allowed origins
    """
    env_origins = os.getenv("ALLOWED_ORIGINS", "")

    if env_origins:
        # Parse comma-separated origins from environment
        origins = [origin.strip() for origin in env_origins.split(",") if origin.strip()]
        return origins

    # Secure defaults for development
    # In production, this should be overridden via environment variable
    return [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
    ]


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate that an API key has a reasonable format.

    Args:
        api_key: API key to validate

    Returns:
        True if format is valid
    """
    if not api_key:
        return False

    # Minimum length check
    if len(api_key) < 20:
        return False

    # Check for common test/placeholder values
    invalid_patterns = [
        "test",
        "demo",
        "placeholder",
        "example",
        "your_key_here",
        "xxx",
        "000",
    ]

    api_key_lower = api_key.lower()
    for pattern in invalid_patterns:
        if pattern in api_key_lower:
            return False

    return True


def create_audit_log_entry(
    event_type: str,
    user_id: Optional[str],
    resource_id: Optional[str],
    action: str,
    result: str,
    details: Optional[dict] = None,
) -> dict:
    """
    Create a structured audit log entry for sensitive operations.

    Args:
        event_type: Type of event (e.g., "PHI_ACCESS", "FILE_UPLOAD")
        user_id: User performing the action
        resource_id: Resource being accessed
        action: Action being performed
        result: Result of the action (e.g., "SUCCESS", "FAILURE")
        details: Additional details

    Returns:
        Structured audit log entry
    """
    import datetime

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id or "SYSTEM",
        "resource_id": resource_id,
        "action": action,
        "result": result,
        "details": details or {},
    }


__all__ = [
    "ALLOWED_EXTENSIONS",
    "MAX_FILE_SIZE",
    "MAX_FILENAME_LENGTH",
    "SecurityError",
    "validate_file_upload",
    "sanitize_filename",
    "generate_secure_id",
    "mask_sensitive_value",
    "hash_phi_value",
    "validate_path_traversal",
    "get_allowed_origins",
    "validate_api_key_format",
    "create_audit_log_entry",
]
