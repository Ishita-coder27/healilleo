from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.vitals import (
    VitalCreate,
    VitalUpdate,
    VitalRead
)
from app.crud import vitals as crud_vitals

router = APIRouter(prefix="/vitals", tags=["Vitals"])

@router.post(
    "/",
    response_model=VitalRead,
    status_code=status.HTTP_201_CREATED
)
def create_vital(
    vital: VitalCreate,
    db: Session = Depends(get_db)
):
    existing = crud_vitals.get_vital_by_key(db, vital.key)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Vital with this key already exists"
        )

    return crud_vitals.create_vital(db, vital)

@router.get("/", response_model=list[VitalRead])
def list_vitals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud_vitals.get_all_vitals(db, skip, limit)

@router.get("/{vital_id}", response_model=VitalRead)
def get_vital(
    vital_id: int,
    db: Session = Depends(get_db)
):
    vital = crud_vitals.get_vital_by_id(db, vital_id)
    if not vital:
        raise HTTPException(status_code=404, detail="Vital not found")
    return vital

@router.patch("/{vital_id}", response_model=VitalRead)
def update_vital(
    vital_id: int,
    vital_data: VitalUpdate,
    db: Session = Depends(get_db)
):
    vital = crud_vitals.update_vital(db, vital_id, vital_data)
    if not vital:
        raise HTTPException(status_code=404, detail="Vital not found")
    return vital

@router.delete("/{vital_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vital(
    vital_id: int,
    db: Session = Depends(get_db)
):
    deleted = crud_vitals.delete_vital(db, vital_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vital not found")
