# Phase 6 — PoC generation + report drafting

## Goal

Extend the triage pipeline beyond severity: turn raw finding evidence into
clean reproduction steps and a structured disclosure report draft.

## Deliverables

- Extend `triage/llm_client.py`'s `LLMClient` interface with
  `generate_poc(finding: dict) -> list[str]` and
  `draft_report(finding: dict) -> str`.
- `triage/poc_generator.py` — takes finding evidence (request/response,
  injection point), asks the LLM for numbered reproduction steps. This is a
  formatting/clarity task on evidence the scanner already captured — the
  prompt should make clear the LLM is not inventing new attack steps, only
  describing the ones already demonstrated.
- `triage/report_writer.py` — structured markdown output: Summary, Impact,
  Steps to Reproduce (pulls from `poc_generator`), Suggested Fix.
- Extend `POST /triage/{finding_id}` to also populate `poc_steps` and a
  `report_draft` field on the finding.
- pytest with mocked `LLMClient`, checking the report has all four required
  sections.

## Out of scope for this phase

- Editing the report draft from the dashboard UI (Phase 7 can add this if
  time allows, otherwise it's a fine v2 item)

## Done when

- A triaged finding has severity, PoC steps, and a report draft, all
  visible via the backend API
