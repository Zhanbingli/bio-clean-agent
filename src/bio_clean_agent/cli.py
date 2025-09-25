from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from .agent import AgentRequest, BioCleaningAgent, SimulatedToolExecutor
from .pipelines import (
    MetabolomicsCleaningPipeline,
    SequencingCleaningPipeline,
    TranscriptomicsCleaningPipeline,
)
from .dataspec.models import load_dataset
from .llm import QwenConfig, QwenLLM, QwenPlanner, SimulatedLLM
from .ui.session import InteractiveSession
from .utils.reporting import save_report

app = typer.Typer(help="Agent CLI for cleaning omics datasets")


def build_agent(output_root: str | Path = "outputs", executor=None) -> BioCleaningAgent:
    agent = BioCleaningAgent(default_output_root=output_root, executor=executor)
    agent.register_pipeline(
        "sequencing",
        lambda dataset, workdir: SequencingCleaningPipeline(executor=agent.executor, output_dir=workdir),
    )
    agent.register_pipeline(
        "transcriptomics",
        lambda dataset, workdir: TranscriptomicsCleaningPipeline(output_dir=workdir),
    )
    agent.register_pipeline(
        "metabolomics",
        lambda dataset, workdir: MetabolomicsCleaningPipeline(output_dir=workdir),
    )
    return agent


def load_request(config_path: Path) -> AgentRequest:
    data = yaml.safe_load(config_path.read_text())
    if "dataset" not in data:
        raise ValueError("Configuration must contain a 'dataset' section")
    return AgentRequest(
        dataset=data["dataset"],
        output_dir=data.get("output_dir"),
        parameters=data.get("parameters"),
    )


@app.command()
def plan(config: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    """Print the plan inferred for a dataset cleaning request."""
    agent = build_agent()
    request = load_request(config)
    dataset = load_dataset(request.dataset["dataset_type"], request.dataset)
    plan_info = agent.plan(dataset, output_dir=request.output_dir, parameters=request.parameters)
    typer.echo(f"Dataset {plan_info['dataset_id']} ({plan_info['dataset_type']})")
    typer.echo(f"Pipeline: {plan_info['pipeline']}")
    typer.echo(f"Working directory: {plan_info['workdir']}")
    typer.echo("Steps:")
    for step in plan_info['steps']:
        typer.echo(f"- {step['name']}: {step['description']}")
    if plan_info['parameters']:
        typer.echo('Parameters:')
        for key, value in plan_info['parameters'].items():
            typer.echo(f"- {key}: {value}")
    if plan_info['warnings']:
        typer.echo('Warnings:')
        for warning in plan_info['warnings']:
            typer.echo(f"- {warning}")

@app.command()
def chat(
    model_path: Optional[str] = typer.Option(None, help="Path or name of the Qwen model"),
    device: str = typer.Option("auto", help="Device mapping for transformers"),
    dtype: Optional[str] = typer.Option(None, help="Optional torch dtype (float16, bfloat16, ...)"),
    load_in_8bit: bool = typer.Option(False, "--load-8bit/--no-load-8bit", help="Load Qwen in 8bit mode"),
    temperature: float = typer.Option(0.1, help="Sampling temperature for the planner"),
    top_p: float = typer.Option(0.9, help="Top-p sampling for the planner"),
    max_new_tokens: int = typer.Option(768, help="Maximum new tokens for each LLM response"),
    dataset_config: Optional[Path] = typer.Option(None, exists=True, readable=True, help="Optional YAML config for dataset execution"),
    auto_execute: bool = typer.Option(False, help="Automatically execute the planned pipeline when a dataset config is present"),
    dry_run: bool = typer.Option(False, help="Use simulated tool executor during chat execution"),
) -> None:
    """Interactive TUI experience powered by Qwen planner."""
    if model_path:
        qwen_config = QwenConfig(
            model_path=model_path,
            device=device,
            dtype=dtype,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            load_in_8bit=load_in_8bit,
        )
        llm = QwenLLM(qwen_config)
    else:
        typer.echo("No model_path provided. Falling back to simulated planner responses.")
        llm = SimulatedLLM()
    planner = QwenPlanner(llm)
    executor = SimulatedToolExecutor() if dry_run else None
    agent = build_agent(executor=executor)
    payload = None
    if dataset_config:
        payload = yaml.safe_load(dataset_config.read_text())
    session = InteractiveSession(agent=agent, planner=planner, dataset_payload=payload)
    session.run(auto_execute=auto_execute)




@app.command()
def run(
    config: Path = typer.Argument(..., exists=True, readable=True),
    report_dir: Optional[Path] = typer.Option(None, help="Directory to save reports"),
    dry_run: bool = typer.Option(False, "--dry-run/--no-dry-run", help="Simulate tool execution without running external binaries"),
) -> None:
    """Execute the cleaning pipeline defined by the configuration."""
    executor = SimulatedToolExecutor() if dry_run else None
    agent = build_agent(executor=executor)
    request = load_request(config)
    dataset = load_dataset(request.dataset["dataset_type"], request.dataset)
    plan_info = agent.plan(dataset, output_dir=request.output_dir, parameters=request.parameters)
    typer.echo(f"Running {plan_info['pipeline']} for dataset {plan_info['dataset_id']}")
    typer.echo("Steps:")
    for step in plan_info['steps']:
        typer.echo(f"- {step['name']}: {step['description']}")
    if plan_info['parameters']:
        typer.echo('Parameters:')
        for key, value in plan_info['parameters'].items():
            typer.echo(f"- {key}: {value}")
    if plan_info['warnings']:
        typer.echo('Warnings:')
        for warning in plan_info['warnings']:
            typer.echo(f"- {warning}")
    if dry_run:
        typer.echo('Dry run enabled: external commands will be simulated.')
    report = agent.run(request)
    typer.echo(f"Pipeline success: {report.success}")
    for step in report.results:
        typer.echo(f"- {step.name}: {'ok' if step.success else 'failed'}")
    if report_dir:
        paths = save_report(report, report_dir)
        typer.echo(f"Reports saved to {paths}")


if __name__ == "__main__":
    app()
