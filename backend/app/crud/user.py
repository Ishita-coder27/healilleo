from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

# --------------------------
# Get all users
# --------------------------
def get_all_users(db: Session):
    return db.query(User).all()

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
        phone_number=user.phone_number,
        emergency_phone_number=user.emergency_phone_number
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

    db.delete(user)
    db.commit()