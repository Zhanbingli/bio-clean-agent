"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
from typing import Dict, Any

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_dataset_config() -> Dict[str, Any]:
    """Sample dataset configuration for testing."""
    return {
        "dataset_id": "test_dataset",
        "dataset_type": "sequencing",
        "raw_paths": ["test_R1.fastq.gz", "test_R2.fastq.gz"],
        "read_type": "paired",
    }


@pytest.fixture
def sample_clinical_trial_config() -> Dict[str, Any]:
    """Sample clinical trial configuration."""
    return {
        "dataset_id": "test_clinical_trial",
        "dataset_type": "clinical_trial",
        "raw_paths": ["test_trial_data.csv"],
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for tests."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "steps": ["Step 1", "Step 2", "Step 3"],
        "parameters": {"quality_threshold": 20},
        "reasoning": "Test reasoning",
    }


# Markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "benchmark: Performance benchmark tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_api_key: Tests requiring API keys")
