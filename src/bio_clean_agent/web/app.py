"""Main FastAPI application for web interface."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..api.jobs import DataType, JobPriority, JobRequest, get_job_manager
from ..knowledge import EvidenceBase, MedicalStandards, ValidationRules
from ..medical import ClinicalTrialHandler
from ..planning import SmartPlanner

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


class JobSubmission(BaseModel):
    """Web job submission model."""

    data_type: str
    objectives: List[str]
    auto_approve: bool = False
    priority: str = "normal"


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="Bio Clean Agent",
        description="Intelligent medical data cleaning with scientific knowledge",
        version="0.3.0",
    )

    # Enable CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create upload directory
    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)

    OUTPUT_DIR = Path("outputs")
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Serve static files
    STATIC_DIR = Path(__file__).parent / "static"
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve main page."""
        html_file = STATIC_DIR / "index.html"
        if html_file.exists():
            return FileResponse(html_file)
        return HTMLResponse(get_simple_html())

    @app.get("/health")
    async def health():
        """Health check."""
        return {
            "status": "healthy",
            "version": "0.3.0",
            "features": ["scientific_knowledge", "intelligent_planning", "evidence_based"],
        }

    @app.post("/upload")
    async def upload_file(file: UploadFile = File(...)):
        """Upload data file."""
        if not file.filename:
            raise HTTPException(400, "No file provided")

        # Generate unique filename
        file_id = str(uuid.uuid4())
        ext = Path(file.filename).suffix
        save_path = UPLOAD_DIR / f"{file_id}{ext}"

        # Save file
        content = await file.read()
        save_path.write_bytes(content)

        # Quick preview
        try:
            if ext in {".csv", ".txt"}:
                import pandas as pd
                import numpy as np

                df = pd.read_csv(save_path)
                # Replace NaN with None for JSON serialization
                sample_data = df.head(5).replace({np.nan: None}).to_dict("records")
                preview = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "sample": sample_data,
                }
            else:
                preview = None
        except Exception:
            preview = None

        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "path": str(save_path),
            "preview": preview,
        }

    @app.post("/analyze")
    async def analyze_data(file_id: str):
        """Analyze uploaded data and create intelligent plan."""
        # Find file
        files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
        if not files:
            raise HTTPException(404, "File not found")

        file_path = files[0]

        try:
            # Load data
            handler = ClinicalTrialHandler(file_path)
            handler.load_data()

            # Profile data
            profile = handler.profile_data()

            # Detect issues
            issues = handler.detect_issues()

            # Get medical standards
            standards = MedicalStandards()
            evidence = EvidenceBase()

            # Create intelligent plan
            planner = SmartPlanner()
            plan = planner.create_plan(
                job_id=file_id,
                data_type="clinical_trial",
                objectives=["Analyze and recommend cleaning strategy"],
                data_profile=profile,
            )

            # Get recommendations
            recommendations = []
            for issue in issues[:5]:  # Top 5 issues
                rec = evidence.get_cleaning_recommendation(
                    issue["category"], context=issue
                )
                if rec:
                    recommendations.append(
                        {
                            "issue": issue["message"],
                            "recommendation": rec.statement,
                            "rationale": rec.rationale,
                            "confidence": rec.confidence.value,
                            "evidence_level": rec.evidence_level.value,
                        }
                    )

            return {
                "file_id": file_id,
                "profile": {
                    "total_records": profile["total_records"],
                    "total_columns": profile["total_columns"],
                    "missing_values": len(profile.get("missing_values", {})),
                },
                "issues": [
                    {
                        "severity": issue["severity"],
                        "category": issue["category"],
                        "message": issue["message"],
                        "field": issue.get("field"),
                    }
                    for issue in issues
                ],
                "plan": {
                    "total_steps": len(plan.steps),
                    "critical_steps": sum(1 for s in plan.steps if s.priority.value == "critical"),
                    "evidence_based_steps": sum(1 for s in plan.steps if s.evidence_based),
                    "estimated_quality_improvement": plan.estimated_quality_improvement,
                    "estimated_data_loss": plan.estimated_data_loss,
                    "steps": [
                        {
                            "name": step.name,
                            "description": step.description,
                            "priority": step.priority.value,
                            "evidence_based": step.evidence_based,
                            "evidence": step.evidence_summary,
                            "risk": step.risk_level,
                        }
                        for step in plan.steps
                    ],
                },
                "recommendations": recommendations,
            }

        except Exception as e:
            raise HTTPException(500, f"Analysis failed: {str(e)}")

    @app.post("/jobs")
    async def submit_job(submission: JobSubmission, file_id: str):
        """Submit cleaning job."""
        # Find file
        files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
        if not files:
            raise HTTPException(404, "File not found")

        job_request = JobRequest(
            data_type=DataType(submission.data_type),
            input_paths=[str(files[0])],
            output_dir=str(OUTPUT_DIR / file_id),
            objectives=submission.objectives,
            auto_approve=submission.auto_approve,
            priority=JobPriority(submission.priority),
        )

        job_manager = get_job_manager()
        job_id = job_manager.submit(job_request)

        return {"job_id": job_id, "status": "submitted"}

    @app.get("/jobs/{job_id}")
    async def get_job_status(job_id: str):
        """Get job status."""
        job_manager = get_job_manager()
        status = job_manager.get_status(job_id)

        if not status:
            raise HTTPException(404, "Job not found")

        return status

    @app.get("/jobs")
    async def list_jobs(limit: int = 50):
        """List all jobs."""
        job_manager = get_job_manager()
        jobs = job_manager.list_jobs(limit=limit)
        return {"jobs": jobs, "count": len(jobs)}

    @app.get("/knowledge/standards")
    async def get_medical_standards():
        """Get available medical standards."""
        standards = MedicalStandards()
        entries = list(standards.entries.values())[:20]  # Return first 20

        return {
            "total": len(standards.entries),
            "standards": [
                {
                    "id": e.id,
                    "category": e.category,
                    "topic": e.topic,
                    "statement": e.statement,
                    "confidence": e.confidence.value,
                    "evidence_level": e.evidence_level.value,
                    "citations": [
                        {"source": c.source, "year": c.year, "title": c.title}
                        for c in e.citations
                    ],
                }
                for e in entries
            ],
        }

    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket for real-time updates."""
        await websocket.accept()
        active_connections[client_id] = websocket

        try:
            while True:
                # Keep connection alive
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            del active_connections[client_id]

    return app


def get_simple_html() -> str:
    """Get simple HTML interface if static files don't exist."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bio Clean Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 60px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 30px;
        }
        .upload-area:hover {
            background: #f8f9ff;
            border-color: #764ba2;
        }
        .upload-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        .feature {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .feature-icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        .feature h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .feature p {
            color: #666;
            font-size: 14px;
        }
        #result {
            margin-top: 30px;
            padding: 20px;
            background: #f0f7ff;
            border-radius: 10px;
            display: none;
        }
        .loading {
            text-align: center;
            padding: 40px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 Bio Clean Agent</h1>
        <p class="subtitle">Intelligent Medical Data Cleaning with Scientific Knowledge</p>

        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
            <div class="upload-icon">📊</div>
            <p style="font-size: 18px; margin-bottom: 10px;">Click to upload your data</p>
            <p style="color: #999;">Supports CSV, Excel files</p>
            <input type="file" id="fileInput" accept=".csv,.xlsx,.xls" style="display:none">
        </div>

        <div id="result"></div>

        <div class="feature-grid">
            <div class="feature">
                <div class="feature-icon">📚</div>
                <h3>50+ Medical Standards</h3>
                <p>Evidence from AHA, WHO, ADA, FDA</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🧠</div>
                <h3>Intelligent Planning</h3>
                <p>Analyzes and reasons about your data</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🔬</div>
                <h3>Scientific Validation</h3>
                <p>Checks biological plausibility</p>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('fileInput').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Uploading and analyzing... 🔍</p>
                </div>
            `;

            // Upload file
            const formData = new FormData();
            formData.append('file', file);

            try {
                const uploadRes = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const uploadData = await uploadRes.json();

                // Analyze
                const analyzeRes = await fetch(`/analyze?file_id=${uploadData.file_id}`, {
                    method: 'POST'
                });
                const analysis = await analyzeRes.json();

                // Show results
                resultDiv.innerHTML = `
                    <h2 style="color: #667eea; margin-bottom: 20px;">📊 Analysis Complete!</h2>

                    <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h3 style="color: #667eea; margin-bottom: 10px;">Data Profile</h3>
                        <p><strong>Records:</strong> ${analysis.profile.total_records.toLocaleString()}</p>
                        <p><strong>Columns:</strong> ${analysis.profile.total_columns}</p>
                        <p><strong>Issues Found:</strong> ${analysis.issues.length}</p>
                    </div>

                    <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h3 style="color: #667eea; margin-bottom: 10px;">🧠 Intelligent Plan</h3>
                        <p><strong>Total Steps:</strong> ${analysis.plan.total_steps}</p>
                        <p><strong>Evidence-Based:</strong> ${analysis.plan.evidence_based_steps} steps</p>
                        <p><strong>Quality Improvement:</strong> ~${(analysis.plan.estimated_quality_improvement * 100).toFixed(0)}%</p>
                        <p><strong>Data Loss:</strong> ~${(analysis.plan.estimated_data_loss * 100).toFixed(1)}%</p>
                    </div>

                    <div style="background: white; padding: 20px; border-radius: 10px;">
                        <h3 style="color: #667eea; margin-bottom: 10px;">💡 Top Recommendations</h3>
                        ${analysis.recommendations.slice(0, 3).map(rec => `
                            <div style="margin-bottom: 15px; padding: 15px; background: #f8f9ff; border-radius: 5px;">
                                <p style="font-weight: bold; margin-bottom: 5px;">${rec.recommendation}</p>
                                <p style="font-size: 14px; color: #666; margin-bottom: 5px;">${rec.rationale}</p>
                                <p style="font-size: 12px; color: #999;">
                                    Confidence: <strong>${rec.confidence.toUpperCase()}</strong> |
                                    Evidence: ${rec.evidence_level.replace('_', ' ')}
                                </p>
                            </div>
                        `).join('')}
                    </div>

                    <div style="margin-top: 20px; text-align: center;">
                        <p style="color: #666; font-size: 14px;">
                            ✅ This analysis is backed by 50+ medical standards and 70+ evidence-based strategies
                        </p>
                    </div>
                `;
            } catch (error) {
                resultDiv.innerHTML = `
                    <div style="background: #ffe0e0; padding: 20px; border-radius: 10px;">
                        <h3 style="color: #d00;">❌ Error</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        });
    </script>
</body>
</html>
    """
