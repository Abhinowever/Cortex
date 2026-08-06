from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Disclosure, Finding
from backend.schemas import DisclosureCreate, DisclosureRead, DisclosureUpdate, TimelineEventCreate

router = APIRouter(prefix="/disclosures", tags=["disclosures"])


def get_disclosure_or_404(disclosure_id: int, db: Session) -> Disclosure:
    disclosure = db.get(Disclosure, disclosure_id)
    if disclosure is None:
        raise HTTPException(status_code=404, detail="Disclosure not found")
    return disclosure


@router.post("", response_model=DisclosureRead, status_code=status.HTTP_201_CREATED)
async def create_disclosure(payload: DisclosureCreate, db: Session = Depends(get_db)) -> Disclosure:
    if db.get(Finding, payload.finding_id) is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    disclosure = Disclosure(**payload.model_dump())
    db.add(disclosure)
    db.commit()
    db.refresh(disclosure)
    return disclosure


@router.get("", response_model=list[DisclosureRead])
async def list_disclosures(db: Session = Depends(get_db)) -> list[Disclosure]:
    return db.query(Disclosure).order_by(Disclosure.id).all()


@router.get("/{disclosure_id}", response_model=DisclosureRead)
async def get_disclosure(disclosure_id: int, db: Session = Depends(get_db)) -> Disclosure:
    return get_disclosure_or_404(disclosure_id, db)


@router.patch("/{disclosure_id}", response_model=DisclosureRead)
async def update_disclosure(
    disclosure_id: int, payload: DisclosureUpdate, db: Session = Depends(get_db)
) -> Disclosure:
    disclosure = get_disclosure_or_404(disclosure_id, db)
    updates = payload.model_dump(exclude_unset=True)
    if "finding_id" in updates and db.get(Finding, updates["finding_id"]) is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    for field, value in updates.items():
        setattr(disclosure, field, value)
    db.commit()
    db.refresh(disclosure)
    return disclosure


@router.post("/{disclosure_id}/timeline", response_model=DisclosureRead)
async def add_timeline_event(
    disclosure_id: int, payload: TimelineEventCreate, db: Session = Depends(get_db)
) -> Disclosure:
    disclosure = get_disclosure_or_404(disclosure_id, db)
    event_time = payload.timestamp or datetime.now(timezone.utc).isoformat()
    new_event = {
        "event": payload.event,
        "timestamp": event_time,
        "notes": payload.notes or ""
    }
    # Update timeline_events JSON list
    current_events = list(disclosure.timeline_events or [])
    current_events.append(new_event)
    disclosure.timeline_events = current_events

    # Also update status if event matches disclosure status keywords
    if payload.event in ["submitted", "acknowledged", "fixed", "disclosed"]:
        disclosure.status = payload.event

    db.commit()
    db.refresh(disclosure)
    return disclosure


@router.delete("/{disclosure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_disclosure(disclosure_id: int, db: Session = Depends(get_db)) -> Response:
    db.delete(get_disclosure_or_404(disclosure_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
