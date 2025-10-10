"""Generate interactive HTML reports for data cleaning jobs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class HTMLReportGenerator:
    """
    Generate interactive, self-contained HTML reports.

    Features:
    - Data quality summary
    - Issues detected and resolved
    - Before/after comparisons
    - Interactive charts (using Chart.js from CDN)
    - Actionable recommendations
    """

    def __init__(self):
        self.template = self._get_template()

    def generate(
        self,
        job_id: str,
        data_type: str,
        profile: Dict[str, Any],
        issues: List[Dict[str, Any]],
        cleaning_summary: Dict[str, Any],
        output_path: str | Path,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Generate comprehensive HTML report.

        Args:
            job_id: Job identifier
            data_type: Type of medical data
            profile: Data profile/summary
            issues: List of detected issues
            cleaning_summary: Summary of cleaning operations
            output_path: Where to save the report
            metadata: Additional metadata to include
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build report sections
        html_content = self.template.format(
            job_id=job_id,
            data_type=data_type,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary_html=self._render_summary(profile, cleaning_summary),
            issues_html=self._render_issues(issues),
            cleaning_html=self._render_cleaning_operations(cleaning_summary),
            recommendations_html=self._render_recommendations(issues, cleaning_summary),
            charts_script=self._render_charts(profile, issues),
        )

        output_path.write_text(html_content, encoding="utf-8")

    def _render_summary(
        self,
        profile: Dict[str, Any],
        cleaning_summary: Dict[str, Any]
    ) -> str:
        """Render data summary section."""
        total_records = profile.get("total_records", 0)
        final_records = cleaning_summary.get("final_record_count", total_records)
        records_removed = total_records - final_records

        html = f"""
        <div class="summary-grid">
            <div class="metric-card">
                <div class="metric-value">{total_records:,}</div>
                <div class="metric-label">Original Records</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{final_records:,}</div>
                <div class="metric-label">Final Records</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{records_removed:,}</div>
                <div class="metric-label">Records Removed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{cleaning_summary.get('total_operations', 0)}</div>
                <div class="metric-label">Cleaning Operations</div>
            </div>
        </div>

        <h3>Data Profile</h3>
        <table class="data-table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Columns</td>
                <td>{profile.get('total_columns', 0)}</td>
            </tr>
            <tr>
                <td>Columns with Missing Values</td>
                <td>{len(profile.get('missing_values', {}))}</td>
            </tr>
            <tr>
                <td>Numeric Columns</td>
                <td>{len(profile.get('numeric_summary', {}))}</td>
            </tr>
            <tr>
                <td>Categorical Columns</td>
                <td>{len(profile.get('categorical_summary', {}))}</td>
            </tr>
        </table>
        """

        # Missing values detail
        missing = profile.get("missing_values", {})
        if missing:
            html += "<h3>Missing Values by Column</h3>"
            html += '<table class="data-table">'
            html += "<tr><th>Column</th><th>Missing Count</th><th>Percentage</th></tr>"
            for col, info in missing.items():
                html += f"""
                <tr>
                    <td>{col}</td>
                    <td>{info['count']}</td>
                    <td>{info['percentage']:.2f}%</td>
                </tr>
                """
            html += "</table>"

        return html

    def _render_issues(self, issues: List[Dict[str, Any]]) -> str:
        """Render issues section."""
        if not issues:
            return '<p class="success">No data quality issues detected.</p>'

        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#17a2b8",
        }

        html = '<div class="issues-list">'
        for issue in issues:
            severity = issue.get("severity", "medium")
            color = severity_colors.get(severity, "#6c757d")

            html += f"""
            <div class="issue-card" style="border-left: 4px solid {color};">
                <div class="issue-header">
                    <span class="issue-severity" style="background-color: {color};">
                        {severity.upper()}
                    </span>
                    <span class="issue-category">{issue.get('category', 'unknown')}</span>
                </div>
                <div class="issue-message">{issue.get('message', '')}</div>
                <div class="issue-details">
                    Field: <code>{issue.get('field', 'N/A')}</code> |
                    Count: {issue.get('count', 0)}
                </div>
            </div>
            """
        html += "</div>"

        return html

    def _render_cleaning_operations(self, summary: Dict[str, Any]) -> str:
        """Render cleaning operations timeline."""
        operations = summary.get("operations", [])

        if not operations:
            return '<p class="info">No cleaning operations performed.</p>'

        html = '<div class="timeline">'
        for i, op in enumerate(operations, start=1):
            html += f"""
            <div class="timeline-item">
                <div class="timeline-marker">{i}</div>
                <div class="timeline-content">
                    <h4>{op.get('action', 'Unknown').replace('_', ' ').title()}</h4>
                    <p>{op.get('details', '')}</p>
                    <div class="timeline-meta">
                        Records affected: {op.get('records_affected', 0)}
                    </div>
                </div>
            </div>
            """
        html += "</div>"

        return html

    def _render_recommendations(
        self,
        issues: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> str:
        """Generate actionable recommendations."""
        recommendations = []

        # Check if there are remaining issues
        unresolved_critical = sum(
            1 for issue in issues
            if issue.get("severity") == "critical"
        )

        if unresolved_critical > 0:
            recommendations.append({
                "priority": "high",
                "title": "Critical Issues Remaining",
                "message": f"{unresolved_critical} critical issues were detected and require attention.",
                "action": "Review the issues section and address critical problems before proceeding with analysis.",
            })

        # Check data loss
        final_count = summary.get("final_record_count", 0)
        total_ops = summary.get("total_operations", 0)

        if total_ops > 0:
            recommendations.append({
                "priority": "medium",
                "title": "Data Quality Improvements Applied",
                "message": f"{total_ops} cleaning operations were performed.",
                "action": "Review the cleaning operations timeline to understand what changed.",
            })

        if not recommendations:
            recommendations.append({
                "priority": "low",
                "title": "Data Quality is Good",
                "message": "No significant issues were detected.",
                "action": "Proceed with your analysis.",
            })

        html = '<div class="recommendations">'
        for rec in recommendations:
            priority_colors = {
                "high": "#dc3545",
                "medium": "#ffc107",
                "low": "#28a745",
            }
            color = priority_colors.get(rec["priority"], "#6c757d")

            html += f"""
            <div class="recommendation-card" style="border-left: 4px solid {color};">
                <h4>{rec['title']}</h4>
                <p>{rec['message']}</p>
                <div class="recommendation-action">
                    <strong>Action:</strong> {rec['action']}
                </div>
            </div>
            """
        html += "</div>"

        return html

    def _render_charts(
        self,
        profile: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> str:
        """Generate Chart.js scripts for interactive visualizations."""
        # Issue severity distribution
        severity_counts = {}
        for issue in issues:
            severity = issue.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return f"""
        // Issue Severity Chart
        const ctx1 = document.getElementById('severityChart').getContext('2d');
        new Chart(ctx1, {{
            type: 'doughnut',
            data: {{
                labels: {list(severity_counts.keys())},
                datasets: [{{
                    data: {list(severity_counts.values())},
                    backgroundColor: ['#dc3545', '#fd7e14', '#ffc107', '#17a2b8'],
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Issues by Severity'
                    }}
                }}
            }}
        }});
        """

    def _get_template(self) -> str:
        """Get HTML template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Cleaning Report - {job_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        h3 {{ color: #555; margin-top: 20px; margin-bottom: 10px; }}
        .header {{ margin-bottom: 30px; }}
        .meta {{ color: #7f8c8d; font-size: 14px; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{ font-size: 32px; font-weight: bold; }}
        .metric-label {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .data-table th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            font-weight: 600;
        }}
        .data-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        .issues-list {{ margin: 20px 0; }}
        .issue-card {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .issue-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        .issue-severity {{
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        .issue-category {{
            color: #6c757d;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .issue-message {{ margin: 10px 0; }}
        .issue-details {{
            color: #6c757d;
            font-size: 13px;
            margin-top: 8px;
        }}
        .timeline {{ margin: 20px 0; }}
        .timeline-item {{
            display: flex;
            margin-bottom: 20px;
        }}
        .timeline-marker {{
            width: 40px;
            height: 40px;
            background: #3498db;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            flex-shrink: 0;
        }}
        .timeline-content {{
            margin-left: 15px;
            flex: 1;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
        }}
        .timeline-content h4 {{ margin-bottom: 5px; color: #2c3e50; }}
        .timeline-meta {{ color: #6c757d; font-size: 13px; margin-top: 8px; }}
        .recommendations {{ margin: 20px 0; }}
        .recommendation-card {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        .recommendation-action {{
            background: #e7f3ff;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .success {{ color: #28a745; padding: 10px; background: #d4edda; border-radius: 4px; }}
        .info {{ color: #0c5460; padding: 10px; background: #d1ecf1; border-radius: 4px; }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Data Cleaning Report</h1>
            <div class="meta">
                Job ID: <code>{job_id}</code> |
                Data Type: {data_type} |
                Generated: {timestamp}
            </div>
        </div>

        <h2>Summary</h2>
        {summary_html}

        <h2>Issues Detected</h2>
        {issues_html}

        <h2>Cleaning Operations</h2>
        {cleaning_html}

        <h2>Recommendations</h2>
        {recommendations_html}

        <h2>Visualizations</h2>
        <canvas id="severityChart" style="max-height: 300px;"></canvas>
    </div>

    <script>
        {charts_script}
    </script>
</body>
</html>
"""
