from sqlalchemy import Column, Integer, String, Text
from app.db.base import Base


class Vital(Base):
    __tablename__ = "vitals"

    id = Column(Integer, primary_key=True, index=True)

    # Stable identifier (slugified name)
    key = Column(String, unique=True, nullable=False, index=True)

    # Human-readable name
    display_name = Column(String, nullable=False)

    # Optional metadata
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)