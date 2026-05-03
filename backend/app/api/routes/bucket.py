# app/api/bucket.py

from fastapi import APIRouter
from app.core.bucket_store import get_bucket_vitals

router = APIRouter()


@router.get("/bucket/{bucket_name}")
def get_bucket(bucket_name: str):
    vitals = get_bucket_vitals(bucket_name)

    if vitals is None:
        return {"error": "Invalid bucket"}

    return {
        "bucket": bucket_name,
        "vitals": vitals
    }