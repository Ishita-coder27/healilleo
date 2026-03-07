from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class UserHealthSnapshot(Base):
    __tablename__ = "user_health_snapshots"

    # One snapshot per user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )

    # Consolidated latest vitals + metadata (LLM-ready)
    vitals_json = Column(JSONB, nullable=False, default=dict)

    # Snapshot bookkeeping
    snapshot_version = Column(Integer, nullable=False, default=1)
    last_updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="health_snapshot")
