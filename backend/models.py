"""SQLAlchemy models for Cortex's core Phase 1 data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    in_scope_domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    out_of_scope_domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    scan_interval_hours: Mapped[int | None] = mapped_column(Integer, default=24, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    scans: Mapped[list["Scan"]] = relationship(back_populates="program", cascade="all, delete-orphan")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"), index=True)
    target_url: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    program: Mapped[Program] = relationship(back_populates="scans")
    findings: Mapped[list["Finding"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int | None] = mapped_column(ForeignKey("scans.id"), nullable=True, index=True)
    vuln_type: Mapped[str] = mapped_column(String(64), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    evidence: Mapped[str] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fingerprint_hash: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    report_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    scan: Mapped[Scan | None] = relationship(back_populates="findings")
    poc_steps: Mapped[list["PocStep"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", order_by="PocStep.step_order"
    )
    disclosures: Mapped[list["Disclosure"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )


class PocStep(Base):
    __tablename__ = "poc_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), index=True)
    step_order: Mapped[int] = mapped_column(Integer)
    instruction: Mapped[str] = mapped_column(Text)

    finding: Mapped[Finding] = relationship(back_populates="poc_steps")


class Disclosure(Base):
    __tablename__ = "disclosures"

    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    program_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cve_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timeline_events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    finding: Mapped[Finding] = relationship(back_populates="disclosures")
