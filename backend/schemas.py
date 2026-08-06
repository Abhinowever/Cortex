"""Pydantic request and response schemas for the Phase 1 API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProgramBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website_url: str | None = None
    in_scope_domains: list[str] = Field(default_factory=list)
    out_of_scope_domains: list[str] = Field(default_factory=list)
    rules: str | None = None
    scan_interval_hours: int | None = 24


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    website_url: str | None = None
    in_scope_domains: list[str] | None = None
    out_of_scope_domains: list[str] | None = None
    rules: str | None = None
    scan_interval_hours: int | None = None


class ProgramRead(ProgramBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ScanCreate(BaseModel):
    program_id: int
    target_url: str = Field(min_length=1, max_length=2048)


class ScanRead(BaseModel):
    id: int
    program_id: int
    target_url: str
    status: str = "pending"
    started_at: datetime
    completed_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PocStepCreate(BaseModel):
    step_order: int
    instruction: str


class PocStepRead(BaseModel):
    id: int
    finding_id: int
    step_order: int
    instruction: str
    model_config = ConfigDict(from_attributes=True)


class FindingBase(BaseModel):
    scan_id: int | None = None
    vuln_type: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=1, max_length=2048)
    evidence: str = Field(min_length=1)
    severity: str | None = None
    fingerprint_hash: str | None = None
    report_draft: str | None = None
    status: str = "new"


class FindingCreate(FindingBase):
    pass


class FindingUpdate(BaseModel):
    scan_id: int | None = None
    vuln_type: str | None = Field(default=None, min_length=1, max_length=64)
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    evidence: str | None = Field(default=None, min_length=1)
    severity: str | None = None
    fingerprint_hash: str | None = None
    report_draft: str | None = None
    status: str | None = None
    poc_steps: list[PocStepCreate] | list[str] | None = None


class FindingRead(FindingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    poc_steps: list[PocStepRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class TimelineEventCreate(BaseModel):
    event: str = Field(description="Event name, e.g. submitted, acknowledged, fixed, disclosed")
    timestamp: str | None = None
    notes: str | None = None


class DisclosureBase(BaseModel):
    finding_id: int
    status: str = "draft"
    program_deadline: datetime | None = None
    cve_id: str | None = None
    timeline_events: list[dict[str, Any]] = Field(default_factory=list)


class DisclosureCreate(DisclosureBase):
    pass


class DisclosureUpdate(BaseModel):
    finding_id: int | None = None
    status: str | None = None
    program_deadline: datetime | None = None
    cve_id: str | None = None
    timeline_events: list[dict[str, Any]] | None = None


class DisclosureRead(DisclosureBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
