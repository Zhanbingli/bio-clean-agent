"""Agent execution guards for missing external tools."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Local import shim
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bio_clean_agent.agent import AgentRequest, BioCleaningAgent, SimulatedToolExecutor  # noqa: E402
from bio_clean_agent.dataspec.models import SequencingDataset  # noqa: E402
from bio_clean_agent.pipelines.sequencing import SequencingCleaningPipeline  # noqa: E402
from bio_clean_agent.utils import preflight  # noqa: E402


def _agent(executor) -> BioCleaningAgent:
    agent = BioCleaningAgent(default_output_root="outputs", executor=executor)
    agent.register_pipeline(
        "sequencing",
        lambda dataset, workdir: SequencingCleaningPipeline(executor=agent.executor, output_dir=workdir),
    )
    return agent


def _dataset(tmp_path: Path) -> SequencingDataset:
    fastq = tmp_path / "reads.fastq"
    fastq.write_text("@id\nACGT\n+\n!!!!\n")
    return SequencingDataset(dataset_id="demo", raw_paths=[str(fastq)], read_type="single", platform=None)


def test_run_fails_when_required_tools_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    agent = _agent(SimulatedToolExecutor())
    dataset = _dataset(tmp_path)
    request = AgentRequest(dataset=dataset.dict(), parameters={})
    monkeypatch.setattr(preflight, "which", lambda name: None)

    with pytest.raises(RuntimeError, match="External tools missing"):
        agent.run(request)


def test_run_can_allow_missing_tools(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    agent = _agent(SimulatedToolExecutor())
    dataset = _dataset(tmp_path)
    request = AgentRequest(dataset=dataset.dict(), parameters={"allow_missing_tools": True})
    monkeypatch.setattr(preflight, "which", lambda name: None)

    report = agent.run(request)

    assert report.success is True
