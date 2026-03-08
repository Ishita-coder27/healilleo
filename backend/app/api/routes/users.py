from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.crud import user as crud_user

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# GET all users
@router.get("/", response_model=list[UserRead])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_user.get_all_users(db, skip=skip, limit=limit)

# GET a user by ID
@router.get("/{user_id}", response_model=UserRead)
def fetch_user(user_id: int, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# POST add a new user
@router.post("/add", response_model=UserRead, status_code=201)
def add_new_user(user: UserCreate, db: Session = Depends(get_db)):
    if crud_user.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    return crud_user.create_user(db, user)

# PATCH update a user
@router.patch("/update/{user_id}", response_model=UserRead)
def update_a_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.email:
        existing_user = crud_user.get_user_by_email(db, user_data.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already exists")

    try:
        return crud_user.update_user(db, user_id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# DELETE a user
@router.delete("/delete/{user_id}", status_code=200)
def delete_a_user(user_id: int, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    crud_user.delete_user(db, user_id)
    return {"detail": "User deleted successfully"}