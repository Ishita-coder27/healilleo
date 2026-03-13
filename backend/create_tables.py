"""
backend/create_tables.py

Run once to create any missing tables:
    python create_tables.py
"""

from app.db.base import Base
from app.db.session import engine

# Import every model so SQLAlchemy registers them before create_all
from app.models.user import User                                    # noqa: F401
from app.models.vitals import Vital                                 # noqa: F401
from app.models.medical_reports import MedicalReport                # noqa: F401
from app.models.report_vitals import ReportVital                    # noqa: F401  (existing junction table — untouched)
from app.models.vital_extraction import VitalExtraction             # noqa: F401  ← new
# from app.models.user_health_snapshot import UserHealthSnapshot    # noqa: F401  (uncomment if you have this)


def create_tables():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. Tables:")
    for t in Base.metadata.tables.keys():
        print(f"  ✅  {t}")


if __name__ == "__main__":
    create_tables()