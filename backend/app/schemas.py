from datetime import datetime
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
    published_at: datetime | None
    summary: str | None
    status: str
    created_at: datetime
    tags: list[TagSchema] = []

    model_config = {"from_attributes": True}


class ArticleListSchema(BaseModel):
    id: int
    title: str
    source_name: str
    published_at: datetime | None
    summary: str | None
    tags: list[TagSchema] = []

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    run_id: int
    status: str
    total_inserted: int
    total_failed: int
