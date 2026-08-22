from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import ForeignKey, Text, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    parsed_text: Mapped[str] = mapped_column(Text, nullable=True)
    extracted_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    extracted_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    
    # Status and tracing columns
    status: Mapped[str] = mapped_column(nullable=False, default="queued")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(nullable=True)
    
    # Ingestion stage timings (durations in seconds)
    parsing_duration: Mapped[float] = mapped_column(nullable=True)
    extraction_duration: Mapped[float] = mapped_column(nullable=True)
    indexing_duration: Mapped[float] = mapped_column(nullable=True)
    verification_duration: Mapped[float] = mapped_column(nullable=True)
    total_duration: Mapped[float] = mapped_column(nullable=True)

    # Relationships
    chunks: Mapped[List["ResumeChunk"]] = relationship(
        "ResumeChunk", back_populates="resume", cascade="all, delete-orphan"
    )

class ResumeChunk(Base):
    __tablename__ = "resume_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(JSON, nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="chunks")
