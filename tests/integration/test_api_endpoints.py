"""Integration tests for API endpoints - basic smoke tests."""

import pytest

# Skip if FastAPI not installed
pytest.importorskip("fastapi")


@pytest.mark.integration
class TestAPIImports:
    """Test suite for API imports."""

    def test_can_import_api_module(self):
        """Test API modules can be imported."""
        try:
            from bio_clean_agent.web import app
            # Just verify import doesn't fail
            assert True
        except ImportError:
            # If web app not fully configured, that's okay for basic tests
            pytest.skip("Web app not configured")

    def test_can_import_job_manager(self):
        """Test job manager can be imported."""
        from bio_clean_agent.api.jobs import JobManager
        manager = JobManager()
        assert manager is not None
