from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --------------------------
# Get all users
# --------------------------
def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

# --------------------------
# Get user by ID
# --------------------------
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# --------------------------
# Get user by email
# --------------------------
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# --------------------------
# Create a new user
# --------------------------
def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
        age=user.age,
        gender=user.gender,
        phone_number=user.phone_number,
        emergency_phone_number=user.emergency_phone_number,
        hashed_password=pwd_context.hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --------------------------
# Update a user
# --------------------------
def update_user(db: Session, user_id: int, user_data: UserUpdate):
    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        return None

    user = get_user_by_id(db, user_id)
    if not user:
        return None

    # Cross-field phone conflict check using resolved final values
    final_phone = update_data.get("phone_number", user.phone_number)
    final_emergency = update_data.get("emergency_phone_number", user.emergency_phone_number)

    if final_emergency and final_phone == final_emergency:
        raise ValueError("Emergency contact must be different from primary number")

    db.query(User)\
      .filter(User.id == user_id)\
      .update(update_data)

    db.commit()
    return db.query(User).filter(User.id == user_id).first()

# --------------------------
# Delete a user
# --------------------------
def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    db.delete(user)
    db.commit()
    return True