from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Finding, PocStep
from backend.schemas import FindingCreate, FindingRead, FindingUpdate, PocStepCreate

router = APIRouter(prefix="/findings", tags=["findings"])


def get_finding_or_404(finding_id: int, db: Session) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.post("", response_model=FindingRead, status_code=status.HTTP_201_CREATED)
async def create_finding(payload: FindingCreate, db: Session = Depends(get_db)) -> Finding:
    finding = Finding(**payload.model_dump())
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


@router.get("", response_model=list[FindingRead])
async def list_findings(
    status: str | None = None, vuln_type: str | None = None, db: Session = Depends(get_db)
) -> list[Finding]:
    query = db.query(Finding)
    if status is not None:
        query = query.filter(Finding.status == status)
    if vuln_type is not None:
        query = query.filter(Finding.vuln_type == vuln_type)
    return query.order_by(Finding.id).all()


@router.get("/{finding_id}", response_model=FindingRead)
async def get_finding(finding_id: int, db: Session = Depends(get_db)) -> Finding:
    return get_finding_or_404(finding_id, db)


@router.patch("/{finding_id}", response_model=FindingRead)
async def update_finding(finding_id: int, payload: FindingUpdate, db: Session = Depends(get_db)) -> Finding:
    finding = get_finding_or_404(finding_id, db)
    update_data = payload.model_dump(exclude_unset=True)

    if "poc_steps" in update_data:
        poc_steps_data = update_data.pop("poc_steps")
        if poc_steps_data is not None:
            db.query(PocStep).filter(PocStep.finding_id == finding_id).delete()
            for idx, item in enumerate(poc_steps_data, start=1):
                instruction = item.get("instruction") if isinstance(item, dict) else str(item)
                step_order = item.get("step_order", idx) if isinstance(item, dict) else idx
                db.add(PocStep(finding_id=finding_id, step_order=step_order, instruction=instruction))

    for field, value in update_data.items():
        setattr(finding, field, value)
    db.commit()
    db.refresh(finding)
    return finding


@router.delete("/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(finding_id: int, db: Session = Depends(get_db)) -> Response:
    db.delete(get_finding_or_404(finding_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
