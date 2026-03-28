from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Article
from app.schemas import ArticleSchema, ArticleListSchema

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=list[ArticleListSchema])
def list_articles(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    articles = (
        db.query(Article)
        .order_by(Article.published_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return articles


@router.get("/{article_id}", response_model=ArticleSchema)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
