# app/services/vital_service.py

from app.core.bucket_store import mark_vital_present, mark_vital_absent
from app.crud import vital_crud  # assuming you have this


def insert_vital(vital_name: str, user_id: int):
    # DB insert
    vital_crud.insert_vital(user_id, vital_name)

    # Update cache
    mark_vital_present(vital_name)


def delete_vital(vital_name: str, user_id: int):
    # DB delete
    vital_crud.delete_vital(user_id, vital_name)

    # Update cache
    mark_vital_absent(vital_name)