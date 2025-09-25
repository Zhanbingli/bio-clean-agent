from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from ..pipelines.base import PipelineReport


def report_to_markdown(report: PipelineReport) -> str:
    lines = [f"# Cleaning Report: {report.pipeline_name}", f"Dataset: {report.dataset_id}"]
    lines.append(f"Status: {'✅ Success' if report.success else '❌ Failed'}")
    lines.append("")
    for step in report.results:
        lines.append(f"## Step: {step.name}")
        lines.append(f"Outcome: {'success' if step.success else 'failed'}")
        if step.details:
            for key, value in step.details.items():
                lines.append(f"- {key}: {value}")
        if step.error:
            lines.append(f"- error: {step.error}")
        lines.append("")
    return "\n".join(lines)


def save_report(report: PipelineReport, output_dir: str | Path) -> Dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"{report.dataset_id}_{report.pipeline_name}.md"
    md_path.write_text(report_to_markdown(report), encoding="utf-8")

    df = pd.DataFrame([step.__dict__ for step in report.results])
    csv_path = output_dir / f"{report.dataset_id}_{report.pipeline_name}.csv"
    df.to_csv(csv_path, index=False)

    return {"markdown": str(md_path), "csv": str(csv_path)}
