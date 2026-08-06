"""FastAPI router for Scans resource."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Program, Scan
from backend.schemas import ScanCreate, ScanRead
from scanner.scope import is_in_scope

router = APIRouter(prefix="/scans", tags=["scans"])


def get_scan_or_404(scan_id: int, db: Session) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("", response_model=ScanRead, status_code=status.HTTP_201_CREATED)
async def create_scan(payload: ScanCreate, db: Session = Depends(get_db)) -> Scan:
    program = db.get(Program, payload.program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")

    # Scope discipline check
    if not is_in_scope(payload.target_url, program.in_scope_domains, program.out_of_scope_domains):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target URL '{payload.target_url}' is out of scope for program '{program.name}'"
        )

    scan = Scan(
        program_id=payload.program_id,
        target_url=payload.target_url,
        status="pending"
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get("", response_model=list[ScanRead])
async def list_scans(
    program_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db)
) -> list[Scan]:
    query = db.query(Scan)
    if program_id is not None:
        query = query.filter(Scan.program_id == program_id)
    if status is not None:
        query = query.filter(Scan.status == status)
    return query.order_by(Scan.id.desc()).all()


@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan(scan_id: int, db: Session = Depends(get_db)) -> Scan:
    return get_scan_or_404(scan_id, db)
