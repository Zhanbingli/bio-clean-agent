"""Preflight check behaviors for pipelines."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure local src is importable without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bio_clean_agent.dataspec.models import SequencingDataset  # noqa: E402
from bio_clean_agent.utils import preflight  # noqa: E402


def _make_sequencing_dataset(tmp_path: Path) -> SequencingDataset:
    fastq = tmp_path / "reads.fastq"
    fastq.write_text("@id\nACGT\n+\n!!!!\n")
    return SequencingDataset(
        dataset_id="demo",
        raw_paths=[str(fastq)],
        read_type="single",
        platform=None,
    )


def test_warns_when_required_tools_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dataset = _make_sequencing_dataset(tmp_path)
    monkeypatch.setattr(preflight, "which", lambda name: None)

    warnings = preflight.run_preflight_checks(dataset, parameters={})

    assert any("External tools missing from PATH" in item for item in warnings)
    assert any("fastqc" in item for item in warnings)
    assert any("cutadapt" in item for item in warnings)


def test_tool_warnings_can_be_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dataset = _make_sequencing_dataset(tmp_path)
    monkeypatch.setattr(preflight, "which", lambda name: None)

    warnings = preflight.run_preflight_checks(dataset, parameters={"skip_tool_checks": True})

    assert all("External tools missing from PATH" not in item for item in warnings)
