from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import typer
import yaml

from .agent import AgentPlan, AgentRequest, BioCleaningAgent, SimulatedToolExecutor
from .pipelines import (
    MetabolomicsCleaningPipeline,
    SequencingCleaningPipeline,
    TranscriptomicsCleaningPipeline,
)
from .dataspec.models import DATASET_MODEL_MAP, load_dataset
from .llm import (
    DEFAULT_LLM_REGISTRY,
    GenerationConfig,
    LLMPlanner,
    LLMProviderError,
    ModelConfig,
    PlannerConfig,
)
from .ui.session import InteractiveSession
from .utils.reporting import save_report
from .wizard import build_context, guess_dataset_type, suggest_parameters

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


def _print_plan(plan: AgentPlan) -> None:
    typer.echo(f"Dataset {plan.dataset_id} ({plan.dataset_type})")
    typer.echo(f"Pipeline: {plan.pipeline}")
    typer.echo(f"Working directory: {plan.workdir}")
    typer.echo("Steps:")
    for step in plan.steps:
        typer.echo(f"- {step.name}: {step.description}")
    if plan.parameters:
        typer.echo("Parameters:")
        for key, value in plan.parameters.items():
            typer.echo(f"- {key}: {value}")
    if plan.warnings:
        typer.echo("Warnings:")
        for warning in plan.warnings:
            typer.echo(f"- {warning}")


def _collect_dataset_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        raise typer.BadParameter(f"Path not found: {path}")
    files = sorted([item for item in path.iterdir() if item.is_file()])
    if not files:
        raise typer.BadParameter(f"No files detected in directory {path}")
    return files


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
def init(
    dataset_path: Path = typer.Argument(..., help="Path to a dataset file or directory"),
    dataset_type: Optional[str] = typer.Option(None, help="Dataset type override"),
    dataset_id: Optional[str] = typer.Option(None, help="Identifier for the dataset"),
    output_dir: Optional[Path] = typer.Option(None, help="Directory for pipeline outputs"),
    report_dir: Optional[Path] = typer.Option(None, help="Directory for generated reports"),
    config_path: Optional[Path] = typer.Option(None, help="Where to write the YAML configuration"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing configuration"),
) -> None:
    """Interactive helper to scaffold a dataset configuration file."""

    files = _collect_dataset_files(dataset_path)
    guess = guess_dataset_type(files)
    allowed_types = sorted(DATASET_MODEL_MAP)

    target_type = dataset_type or guess
    if target_type not in allowed_types:
        prompt_default = guess or "sequencing"
        target_type = typer.prompt(
            "Dataset type",
            default=prompt_default,
        ).strip().lower()
    if target_type not in allowed_types:
        raise typer.BadParameter(f"Unsupported dataset type '{target_type}'. Choose from {allowed_types}")

    suggested_id = dataset_id or files[0].stem.replace(" ", "_")
    target_id = typer.prompt("Dataset identifier", default=suggested_id).strip()

    default_output = output_dir or Path("outputs") / target_id
    out_dir = Path(typer.prompt("Output directory", default=str(default_output))).expanduser().resolve()

    if report_dir is not None:
        report_path = Path(report_dir).expanduser().resolve() if report_dir else None
    else:
        report_default = str(Path("reports"))
        report_input = typer.prompt(
            "Report directory (leave blank to skip)",
            default=report_default,
        )
        report_path = Path(report_input).expanduser().resolve() if report_input else None

    extras: Dict[str, object] = {}
    if target_type == "sequencing":
        read_type_default = "paired" if len(files) == 2 else "single"
        read_type = typer.prompt("Read type (single/paired)", default=read_type_default)
        extras["read_type"] = read_type.lower()
        platform = typer.prompt("Sequencing platform (optional)", default="")
        if platform:
            extras["platform"] = platform
    elif target_type == "transcriptomics":
        matrix_format = typer.prompt("Matrix format (counts/tpm/fpkm)", default="counts")
        extras["matrix_format"] = matrix_format
        annotation = typer.prompt("Gene annotation file (optional)", default="")
        if annotation:
            extras["gene_annotation"] = annotation
    elif target_type == "metabolomics":
        platform = typer.prompt("Analytical platform (optional)", default="")
        if platform:
            extras["analytical_platform"] = platform
        ion_mode = typer.prompt("Ion mode (positive/negative, optional)", default="")
        if ion_mode:
            extras["ion_mode"] = ion_mode.lower()

    parameters = suggest_parameters(target_type, str(files[0]))
    typer.echo("Suggested parameters:")
    for key, value in parameters.items():
        typer.echo(f"  - {key}: {value}")
    if typer.confirm("Would you like to edit parameters?", default=False):
        while True:
            key = typer.prompt("Parameter key (blank to finish)", default="")
            if not key:
                break
            value = typer.prompt(f"Value for {key}")
            parameters[key] = value

    context = build_context(
        dataset_paths=[str(path) for path in files],
        dataset_type=target_type,
        dataset_id=target_id,
        output_dir=out_dir,
        report_dir=report_path,
        parameters={k: v for k, v in parameters.items() if k != "detected_delimiter"},
        extras=extras,
    )

    destination = (config_path or Path("configs") / f"{target_id}.yaml").expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        raise typer.BadParameter(f"Config {destination} already exists. Use --force to overwrite.")

    with destination.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(context.to_dict(), handle, sort_keys=False, allow_unicode=True)

    typer.echo(f"Configuration written to {destination}")

    delimiter = parameters.get("detected_delimiter")
    if delimiter and delimiter not in {None, ","}:
        typer.echo(
            "⚠️  Detected a non-comma delimiter. Pipelines will auto-detect, but converting"
            " the table to CSV can improve stability."
        )


@app.command()
def models() -> None:
    """List available planner models registered with the agent."""
    registry = DEFAULT_LLM_REGISTRY
    active_key = registry.describe().key
    typer.echo("Available planner models:")
    for descriptor in registry.available_models():
        marker = "*" if descriptor.key == active_key else "-"
        tags = f" tags={','.join(descriptor.tags)}" if descriptor.tags else ""
        typer.echo(f"{marker} {descriptor.key} ({descriptor.provider}) -> {descriptor.name}{tags}")
        typer.echo(f"    {descriptor.description}")


@app.command()
def plan(config: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    """Print the plan inferred for a dataset cleaning request."""
    agent = build_agent()
    request = load_request(config)
    dataset = load_dataset(request.dataset["dataset_type"], request.dataset)
    plan_info = agent.plan(dataset, output_dir=request.output_dir, parameters=request.parameters)
    _print_plan(plan_info)

@app.command()
def chat(
    model_choice: str = typer.Option(
        "auto",
        "--model",
        help="Model key from the registry (use `bio-clean-agent models` to list options).",
    ),
    model_path: Optional[str] = typer.Option(None, help="Optional HF model path for local providers"),
    api_key: Optional[str] = typer.Option(None, help="API key for hosted providers (OpenAI, etc.)"),
    device: str = typer.Option("auto", help="Device mapping for transformers backends"),
    dtype: Optional[str] = typer.Option(None, help="Optional torch dtype (float16, bfloat16, ...)"),
    load_in_8bit: bool = typer.Option(False, "--load-8bit/--no-load-8bit", help="Load transformer weights in 8-bit"),
    temperature: float = typer.Option(0.1, help="Sampling temperature for planner generations"),
    top_p: float = typer.Option(0.9, help="Top-p nucleus sampling for planner generations"),
    max_new_tokens: int = typer.Option(768, help="Maximum new tokens for each planner response"),
    dataset_config: Optional[Path] = typer.Option(None, exists=True, readable=True, help="Optional YAML config for dataset execution"),
    auto_execute: bool = typer.Option(False, help="Automatically execute the planned pipeline when a dataset config is present"),
    dry_run: bool = typer.Option(False, help="Use simulated tool executor during chat execution"),
) -> None:
    """Interactive TUI experience with pluggable planner models."""
    registry = DEFAULT_LLM_REGISTRY
    model_options = {
        "model_path": model_path,
        "hf_model": model_path,
        "device": device,
        "dtype": dtype,
        "load_in_8bit": load_in_8bit,
        "temperature": temperature,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
    }
    clean_options = {key: value for key, value in model_options.items() if value is not None}
    try:
        llm, descriptor = registry.create(ModelConfig(choice=model_choice, options=clean_options, api_key=api_key))
    except LLMProviderError as exc:
        typer.secho(f"Failed to initialise planner model: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    planner_config = PlannerConfig(
        generation=GenerationConfig(temperature=temperature, top_p=top_p, max_new_tokens=max_new_tokens)
    )
    planner = LLMPlanner(llm, config=planner_config, descriptor=descriptor)
    typer.echo(f"Planner model: {descriptor.name} [{descriptor.key}]")
    executor = SimulatedToolExecutor() if dry_run else None
    agent = build_agent(executor=executor)
    payload = None
    if dataset_config:
        payload = yaml.safe_load(dataset_config.read_text())
    session = InteractiveSession(
        agent=agent,
        planner=planner,
        dataset_payload=payload,
        model_registry=registry,
        model_options=dict(clean_options),
        api_key=api_key,
        active_model=descriptor,
    )
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
    _print_plan(plan_info)
    if dry_run:
        typer.echo('Dry run enabled: external commands will be simulated.')
    report = agent.run(request, plan=plan_info)
    typer.echo(f"Pipeline success: {report.success}")
    for step in report.results:
        typer.echo(f"- {step.name}: {'ok' if step.success else 'failed'}")
    if report_dir:
        paths = save_report(report, report_dir)
        typer.echo(f"Reports saved to {paths}")


if __name__ == "__main__":
    app()
