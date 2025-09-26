from __future__ import annotations

from pathlib import Path
from typing import Optional

from bio_clean_agent.agent import AgentPlan, AgentRequest, BioCleaningAgent, SimulatedToolExecutor
from bio_clean_agent.llm import (
    DEFAULT_LLM_REGISTRY,
    GenerationConfig,
    LLMPlanner,
    LLMProviderError,
    ModelConfig,
    PlannerConfig,
    PlannerOutput,
    SimulatedLLM,
)
from bio_clean_agent.dataspec.models import load_dataset
from bio_clean_agent.pipelines import (
    MetabolomicsCleaningPipeline,
    SequencingCleaningPipeline,
    TranscriptomicsCleaningPipeline,
)
from bio_clean_agent.utils.reporting import save_report


def build_agent(executor=None) -> BioCleaningAgent:
    agent = BioCleaningAgent(default_output_root=Path("outputs"), executor=executor)
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


def main(
    config_file: Path,
    dry_run: bool = False,
    prompt: Optional[str] = None,
    model_path: Optional[str] = None,
    temperature: float = 0.1,
    top_p: float = 0.9,
    max_new_tokens: int = 768,
) -> None:
    import yaml

    payload = yaml.safe_load(config_file.read_text())
    request = AgentRequest(
        dataset=payload["dataset"],
        output_dir=payload.get("output_dir"),
        parameters=payload.get("parameters"),
    )
    executor = SimulatedToolExecutor() if dry_run else None
    agent = build_agent(executor=executor)
    dataset = load_dataset(request.dataset["dataset_type"], request.dataset)
    plan_info = agent.plan(dataset, output_dir=request.output_dir, parameters=request.parameters)
    planner_summary: Optional[PlannerOutput] = None
    if prompt:
        registry = DEFAULT_LLM_REGISTRY
        model_choice = "qwen" if model_path else "auto"
        options = {
            "temperature": temperature,
            "top_p": top_p,
            "max_new_tokens": max_new_tokens,
        }
        if model_path:
            options["model_path"] = model_path
        try:
            llm, descriptor = registry.create(ModelConfig(choice=model_choice, options=options))
        except LLMProviderError:
            llm = SimulatedLLM()
            descriptor = None
        planner_config = PlannerConfig(
            generation=GenerationConfig(temperature=temperature, top_p=top_p, max_new_tokens=max_new_tokens)
        )
        planner = LLMPlanner(llm, config=planner_config, descriptor=descriptor)
        bundle = agent.plan_with_llm(prompt, planner, dataset_payload=payload)
        planner_summary = bundle.planner_output
        if bundle.agent_plan:
            plan_info = bundle.agent_plan
        if bundle.merged_parameters:
            request = AgentRequest(
                dataset=request.dataset,
                output_dir=request.output_dir,
                parameters=bundle.merged_parameters,
            )
    if planner_summary:
        print("Planner reasoning:", planner_summary.reasoning)
        actions = planner_summary.actions
        if actions:
            print("LLM suggested actions:")
            for idx, action in enumerate(actions, start=1):
                print(f"  {idx}. {action.get('step')}: {action.get('description')}")
    print(f"Dataset {plan_info.dataset_id} ({plan_info.dataset_type})")
    print(f"Pipeline: {plan_info.pipeline}")
    print("Planned steps:")
    for step in plan_info.steps:
        print(f"- {step.name}: {step.description}")
    if plan_info.parameters:
        print("Parameters:")
        for key, value in plan_info.parameters.items():
            print(f"  - {key}: {value}")
    if plan_info.warnings:
        print("Warnings:")
        for warning in plan_info.warnings:
            print(f"  - {warning}")
    if dry_run:
        print("Dry run enabled: external commands will be simulated.")
    report = agent.run(request, plan=plan_info)
    print(f"Pipeline success: {report.success}")
    for step in report.results:
        print(f"  {step.name}: {'ok' if step.success else 'failed'}")
    save_report(report, Path(payload.get("report_dir", "reports")))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Example runner for the Bio Cleaning Agent")
    parser.add_argument("config", type=Path, help="Path to YAML config file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate tool execution without running external binaries")
    parser.add_argument("--prompt", type=str, help="Optional natural-language goal for the Qwen planner")
    parser.add_argument("--model-path", type=str, help="Optional Qwen model identifier", default=None)
    parser.add_argument("--temperature", type=float, default=0.1, help="Planner sampling temperature")
    parser.add_argument("--top-p", type=float, default=0.9, help="Planner nucleus sampling parameter")
    parser.add_argument("--max-new-tokens", type=int, default=768, help="Planner generation length")
    args = parser.parse_args()
    main(
        args.config,
        dry_run=args.dry_run,
        prompt=args.prompt,
        model_path=args.model_path,
        temperature=args.temperature,
        top_p=args.top_p,
        max_new_tokens=args.max_new_tokens,
    )
