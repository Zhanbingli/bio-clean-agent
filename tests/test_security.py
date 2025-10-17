"""Basic security tests for Bio Clean Agent."""

import sys
from pathlib import Path

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Define pytest.raises mock for manual testing
    class pytest:
        class raises:
            def __init__(self, exception, match=None):
                self.exception = exception
                self.match = match

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    raise AssertionError(f"Expected {self.exception.__name__} but no exception was raised")
                if not issubclass(exc_type, self.exception):
                    return False
                if self.match and self.match not in str(exc_val):
                    raise AssertionError(f"Expected exception message to contain '{self.match}' but got '{exc_val}'")
                return True  # Suppress the exception

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bio_clean_agent.utils.security import (
    validate_file_upload,
    sanitize_filename,
    generate_secure_id,
    mask_sensitive_value,
    hash_phi_value,
    SecurityError,
)


class TestFileUploadValidation:
    """Test file upload security."""

    def test_valid_csv_file(self):
        """Valid CSV file should pass validation."""
        validate_file_upload("data.csv", 1024)  # 1KB
        # No exception = success

    def test_invalid_extension_rejected(self):
        """Files with dangerous extensions should be rejected."""
        with pytest.raises(SecurityError, match="File type not allowed"):
            validate_file_upload("malware.exe", 1024)

    def test_oversized_file_rejected(self):
        """Files exceeding size limit should be rejected."""
        max_size = 100 * 1024 * 1024  # 100MB
        with pytest.raises(SecurityError, match="File too large"):
            validate_file_upload("data.csv", max_size + 1)

    def test_empty_filename_rejected(self):
        """Empty filename should be rejected."""
        with pytest.raises(SecurityError, match="cannot be empty"):
            validate_file_upload("", 1024)


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_normal_filename(self):
        """Normal filename should pass through unchanged."""
        assert sanitize_filename("data.csv") == "data.csv"
        assert sanitize_filename("report_2025.xlsx") == "report_2025.xlsx"

    def test_path_traversal_blocked(self):
        """Path traversal attempts should be sanitized."""
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        # The sanitize_filename removes path and keeps only filename
        assert result == "passwd"

    def test_special_characters_removed(self):
        """Special characters should be replaced with underscores."""
        assert sanitize_filename("file<>name.csv") == "file__name.csv"
        assert sanitize_filename("file:name.csv") == "file_name.csv"

    def test_hidden_files_prevented(self):
        """Hidden files (starting with .) should be prefixed."""
        result = sanitize_filename(".hidden")
        assert not result.startswith(".")
        assert result == "_hidden"


class TestSecureIDGeneration:
    """Test secure ID generation."""

    def test_generates_unique_ids(self):
        """Generated IDs should be unique."""
        id1 = generate_secure_id()
        id2 = generate_secure_id()
        assert id1 != id2

    def test_id_length(self):
        """Generated ID should be 32 characters (16 bytes hex)."""
        secure_id = generate_secure_id()
        assert len(secure_id) == 32

    def test_id_is_hex(self):
        """Generated ID should be valid hexadecimal."""
        secure_id = generate_secure_id()
        int(secure_id, 16)  # Should not raise ValueError


class TestSensitiveValueMasking:
    """Test sensitive value masking."""

    def test_masks_api_key(self):
        """API key should be masked with last 4 chars visible."""
        api_key = "sk-1234567890abcdef1234567890abcdef"
        masked = mask_sensitive_value(api_key)
        assert "****" in masked
        assert masked.endswith("cdef")
        assert "1234567890" not in masked

    def test_short_value_fully_masked(self):
        """Short values should be fully masked."""
        short_key = "abc"
        masked = mask_sensitive_value(short_key)
        assert masked == "********"


class TestPHIHashing:
    """Test PHI value hashing."""

    def test_consistent_hashing(self):
        """Same value should produce same hash."""
        value = "John Doe"
        hash1 = hash_phi_value(value)
        hash2 = hash_phi_value(value)
        assert hash1 == hash2

    def test_different_values_different_hashes(self):
        """Different values should produce different hashes."""
        hash1 = hash_phi_value("John Doe")
        hash2 = hash_phi_value("Jane Smith")
        assert hash1 != hash2

    def test_hash_length(self):
        """SHA-256 hash should be 64 characters."""
        result = hash_phi_value("test")
        assert len(result) == 64

    def test_salt_changes_hash(self):
        """Using different salts should produce different hashes."""
        value = "John Doe"
        hash1 = hash_phi_value(value, salt="salt1")
        hash2 = hash_phi_value(value, salt="salt2")
        assert hash1 != hash2


if __name__ == "__main__":
    # Run tests manually if pytest not installed
    import traceback

    test_classes = [
        TestFileUploadValidation,
        TestFilenameSanitization,
        TestSecureIDGeneration,
        TestSensitiveValueMasking,
        TestPHIHashing,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                method = getattr(instance, method_name)
                try:
                    method()
                    print(f"  ✅ {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ❌ {method_name}: {e}")
                    traceback.print_exc()
                    failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)
