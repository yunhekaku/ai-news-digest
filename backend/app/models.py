from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, nullable=False)
    article_url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending | summarized | failed
    created_at = Column(DateTime, default=datetime.utcnow)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="running")  # running | completed | failed
    total_inserted = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
