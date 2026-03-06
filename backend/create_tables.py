from app.db.session import engine
from app.db.base import Base

# import models so SQLAlchemy knows about them
from app.models import user
from app.models import medical_reports

Base.metadata.create_all(bind=engine)

print("Database tables created successfully")
