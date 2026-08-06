# Phase 4 — Triage pipeline v1 (severity classification only)

## Goal

Take real XSS findings from Phase 3 and classify severity via an LLM,
writing the result back to the finding record. This is the phase that
proves the triage → backend loop, for one capability.

## Deliverables

- `triage/llm_client.py` — abstract `LLMClient` base class with a
  `classify_severity(finding: dict) -> Severity` method. Concrete
  implementation for one provider to start (your choice), selected via
  `LLM_PROVIDER` env var. Do not import a specific provider's SDK anywhere
  outside this file.
- `triage/classifier.py` — takes a finding, builds the prompt (include vuln
  type, url, evidence/request-response pair), calls `LLMClient`, parses a
  structured (JSON) severity + justification back.
- `triage/main.py` — FastAPI entrypoint: `POST /triage/{finding_id}` pulls
  the finding from the backend, classifies it, PATCHes the severity back.
- Prompt should request CVSS-aligned severity (Critical/High/Medium/Low)
  with a short justification string.
- pytest with a mocked `LLMClient` (do not hit a real API in tests).

## Out of scope for this phase

- Dedup (Phase 7)
- PoC generation, report drafting (Phase 6)
- Calling this automatically after a scan (wire that up once both sides are
  proven — for now, trigger it manually via the endpoint)

## Done when

- `POST /triage/{finding_id}` on a real Phase 3 finding updates its severity
  field, visible via `GET /findings` on the backend
- Swapping `LLM_PROVIDER` doesn't require touching `classifier.py`
