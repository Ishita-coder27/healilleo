from sqlalchemy.orm import Session
from app.models.vitals import Vital
from app.schemas.vitals import VitalCreate, VitalUpdate


# -------- Create --------
def create_vital(db: Session, vital_data: VitalCreate) -> Vital:
    vital = Vital(**vital_data.model_dump())
    db.add(vital)
    db.commit()
    db.refresh(vital)
    return vital


# -------- Read --------
def get_vital_by_id(db: Session, vital_id: int) -> Vital | None:
    return db.query(Vital).filter(Vital.id == vital_id).first()


def get_vital_by_key(db: Session, key: str) -> Vital | None:
    return db.query(Vital).filter(Vital.key == key).first()


def get_all_vitals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Vital).offset(skip).limit(limit).all()


# -------- Update --------
def update_vital(
    db: Session,
    vital_id: int,
    vital_data: VitalUpdate
) -> Vital | None:
    vital = get_vital_by_id(db, vital_id)
    if not vital:
        return None

    update_data = vital_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(vital, field, value)

    db.commit()
    db.refresh(vital)
    return vital


# -------- Delete --------
def delete_vital(db: Session, vital_id: int) -> bool:
    vital = get_vital_by_id(db, vital_id)
    if not vital:
        return False

    db.delete(vital)
    db.commit()
    return True
