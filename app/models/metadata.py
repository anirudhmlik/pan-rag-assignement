#/app/models/metadata.py

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    num_pages = Column(Integer)
    status = Column(String, default="processing") # e.g., 'processing', 'completed', 'failed'

    chunks = relationship("Chunk", back_populates="document")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer)
    chunk_index = Column(Integer)
    vector_id = Column(String, unique=True, nullable=True) # ID from vector DB

    document = relationship("Document", back_populates="chunks")

# Create tables (call this from a startup script or main.py if needed, or migration tool)
def init_db():
    Base.metadata.create_all(bind=engine)

# Pydantic models for API request/response validation (optional, but good practice)
from pydantic import BaseModel
from typing import Optional, List

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    uploaded_at: datetime
    num_pages: Optional[int]
    status: str

    class Config:
        from_attributes = True

class ChunkMetadata(BaseModel):
    id: str
    document_id: str
    page_number: Optional[int]
    chunk_index: Optional[int]
    chunk_text: str # Usually not exposed via API, but good for internal use
    vector_id: Optional[str]

    class Config:
        from_attributes = True