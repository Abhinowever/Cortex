from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Program
from backend.schemas import ProgramCreate, ProgramRead, ProgramUpdate

router = APIRouter(prefix="/programs", tags=["programs"])


def get_program_or_404(program_id: int, db: Session) -> Program:
    program = db.get(Program, program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@router.post("", response_model=ProgramRead, status_code=status.HTTP_201_CREATED)
async def create_program(payload: ProgramCreate, db: Session = Depends(get_db)) -> Program:
    program = Program(**payload.model_dump())
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


@router.get("", response_model=list[ProgramRead])
async def list_programs(db: Session = Depends(get_db)) -> list[Program]:
    return db.query(Program).order_by(Program.id).all()


@router.get("/{program_id}", response_model=ProgramRead)
async def get_program(program_id: int, db: Session = Depends(get_db)) -> Program:
    return get_program_or_404(program_id, db)


@router.patch("/{program_id}", response_model=ProgramRead)
async def update_program(program_id: int, payload: ProgramUpdate, db: Session = Depends(get_db)) -> Program:
    program = get_program_or_404(program_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(program, field, value)
    db.commit()
    db.refresh(program)
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(program_id: int, db: Session = Depends(get_db)) -> Response:
    db.delete(get_program_or_404(program_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
