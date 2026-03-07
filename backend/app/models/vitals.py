from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base


class Vital(Base):
    __tablename__ = "vitals"

    id = Column(Integer, primary_key=True, index=True)

    # Stable identifier (used in code / LLM prompts)
    key = Column(String, unique=True, nullable=False, index=True)
    # Human-readable name
    display_name = Column(String, nullable=False)

    # Medical metadata
    unit = Column(String, nullable=True)
    normal_range = Column(JSONB, nullable=True)  # {"min": 12, "max": 16}
    category = Column(String, nullable=True)     # blood, cardiac, metabolic
    description = Column(Text, nullable=True)
