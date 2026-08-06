"""FastAPI entrypoint for Cortex triage service."""

import os
import httpx
from fastapi import FastAPI, HTTPException

from triage.classifier import SeverityClassifier
from triage.poc_generator import PocGenerator
from triage.report_writer import ReportWriter
from triage.dedup import Deduplicator
from triage.llm_client import get_llm_client

app = FastAPI(title="Cortex Triage Service")


@app.post("/triage/{finding_id}")
async def triage_finding(finding_id: int):
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
    llm_client = get_llm_client()

    async with httpx.AsyncClient() as client:
        # 1. Pull finding from backend
        get_resp = await client.get(f"{backend_url}/findings/{finding_id}")
        if get_resp.status_code != 200:
            raise HTTPException(status_code=get_resp.status_code, detail=f"Failed to fetch finding {finding_id}: {get_resp.text}")

        finding_data = get_resp.json()

        # 1b. Check deduplication against existing findings in backend (Pass 1 hash + Pass 2 LLM)
        all_resp = await client.get(f"{backend_url}/findings")
        if all_resp.status_code == 200:
            existing_findings = all_resp.json()
            if isinstance(existing_findings, list):
                deduplicator = Deduplicator(client=llm_client)
                is_dup, orig_id = await deduplicator.deduplicate(finding_data, existing_findings)
                if is_dup:
                    patch_payload = {
                        "severity": "Duplicate",
                        "report_draft": f"Duplicate finding of #{orig_id}",
                        "status": "duplicate"
                    }
                    patch_resp = await client.patch(f"{backend_url}/findings/{finding_id}", json=patch_payload)
                    return {
                        "status": "duplicate",
                        "finding_id": finding_id,
                        "original_finding_id": orig_id,
                        "updated_finding": patch_resp.json() if patch_resp.status_code == 200 else finding_data
                    }



        # 2. Classify severity
        classifier = SeverityClassifier(client=llm_client)
        severity_res = await classifier.classify(finding_data)
        severity_value = f"{severity_res.severity} - {severity_res.justification}"

        # 3. Generate PoC reproduction steps
        poc_generator = PocGenerator(client=llm_client)
        poc_steps = await poc_generator.generate_steps(finding_data)

        # 4. Draft markdown disclosure report
        report_writer = ReportWriter(client=llm_client)
        report_draft = await report_writer.draft(finding_data, poc_steps)

        # 5. PATCH finding in backend with severity, poc_steps, report_draft, and status
        patch_payload = {
            "severity": severity_value,
            "poc_steps": poc_steps,
            "report_draft": report_draft,
            "status": "triaged"
        }

        patch_resp = await client.patch(f"{backend_url}/findings/{finding_id}", json=patch_payload)
        if patch_resp.status_code != 200:
            raise HTTPException(status_code=patch_resp.status_code, detail=f"Failed to update finding {finding_id}: {patch_resp.text}")

        return {
            "status": "success",
            "finding_id": finding_id,
            "severity": severity_res.severity,
            "justification": severity_res.justification,
            "poc_steps": poc_steps,
            "report_draft": report_draft,
            "updated_finding": patch_resp.json()
        }
