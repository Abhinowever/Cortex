"""FastAPI entrypoint for Cortex scanner service."""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from scanner.engine import ScanEngine

app = FastAPI(title="Cortex Scanner Service")


class ScanRequest(BaseModel):
    target_url: str = Field(..., min_length=1)
    program_id: int


@app.post("/scan")
async def trigger_scan(req: ScanRequest):
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    engine = ScanEngine(backend_url=backend_url)
    try:
        findings = await engine.run_scan(target_url=req.target_url, program_id=req.program_id)
        return {"status": "success", "findings_count": len(findings), "findings": findings}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
