from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TagSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ArticleSchema(BaseModel):
    id: int
    source_name: str
    article_url: str
    title: str
    published_at: Optional[datetime]
    summary: Optional[str]
    status: str
    created_at: datetime
    tags: List[TagSchema] = []

    model_config = {"from_attributes": True}


class ArticleListSchema(BaseModel):
    id: int
    title: str
    source_name: str
    published_at: Optional[datetime]
    summary: Optional[str]
    tags: List[TagSchema] = []

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    run_id: int
    status: str
    total_inserted: int
    total_failed: int
