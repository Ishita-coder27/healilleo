from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.schemas.medications import MedicationCreate, MedicationUpdate, MedicationRead
from app.crud import medications as crud

router = APIRouter(prefix="/medications", tags=["Medications"])

@router.post("/", response_model=MedicationRead, status_code=201)
def create(data: MedicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_medication(db, current_user.id, data)

@router.get("/", response_model=list[MedicationRead])
def get_all(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_medications_by_user(db, current_user.id)

@router.get("/{medication_id}", response_model=MedicationRead)
def get_one(medication_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    med = crud.get_medication_by_id(db, medication_id)
    if not med or med.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medication not found")
    return med

@router.put("/{medication_id}", response_model=MedicationRead)
def update(medication_id: int, data: MedicationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    med = crud.get_medication_by_id(db, medication_id)
    if not med or med.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medication not found")
    return crud.update_medication(db, medication_id, data)

@router.delete("/{medication_id}", status_code=200)
def delete(medication_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    med = crud.get_medication_by_id(db, medication_id)
    if not med or med.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medication not found")
    crud.delete_medication(db, medication_id)
    return {"detail": "Medication deleted"}

@router.get("/reminders/due", response_model=list[MedicationRead])
def get_due_reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    all_due = crud.get_upcoming_medication_reminders(db)
    return [m for m in all_due if m.user_id == current_user.id]