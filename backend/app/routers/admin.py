import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db, settings
from app.models import Article, IngestionRun
from app.schemas import IngestResponse

import feedparser
import httpx
from bs4 import BeautifulSoup
import anthropic

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

RSS_FEEDS = [
    "https://feeds.feedburner.com/oreilly/radar",
    "https://openai.com/blog/rss/",
    "https://www.anthropic.com/news/rss",
]


def fetch_articles_from_feeds() -> list[dict]:
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                articles.append({
                    "source_name": feed.feed.get("title", url),
                    "article_url": entry.get("link", ""),
                    "title": entry.get("title", ""),
                    "published_at": entry.get("published_parsed"),
                })
        except Exception as e:
            logger.error(f"Failed to fetch feed {url}: {e}")
    return articles


def extract_text(url: str) -> str:
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:4000]
    except Exception as e:
        logger.error(f"Failed to extract text from {url}: {e}")
        return ""


def summarize(text: str) -> str:
    if not settings.anthropic_api_key or not text:
        return ""
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"以下の英語記事を日本語で3〜5文に要約してください。\n\n{text}",
            }],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return ""


@router.post("/ingest", response_model=IngestResponse)
def ingest(db: Session = Depends(get_db)):
    run = IngestionRun(started_at=datetime.utcnow(), status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    inserted = 0
    failed = 0

    raw_articles = fetch_articles_from_feeds()
    for raw in raw_articles:
        if not raw["article_url"]:
            failed += 1
            continue
        existing = db.query(Article).filter(Article.article_url == raw["article_url"]).first()
        if existing:
            continue
        try:
            text = extract_text(raw["article_url"])
            summary = summarize(text)
            pub = None
            if raw["published_at"]:
                pub = datetime(*raw["published_at"][:6])
            article = Article(
                source_name=raw["source_name"],
                article_url=raw["article_url"],
                title=raw["title"],
                published_at=pub,
                summary=summary,
                status="summarized" if summary else "pending",
            )
            db.add(article)
            db.commit()
            inserted += 1
        except Exception as e:
            logger.error(f"Failed to process article {raw['article_url']}: {e}")
            failed += 1

    run.status = "completed"
    run.total_inserted = inserted
    run.total_failed = failed
    db.commit()
    db.refresh(run)

    return IngestResponse(
        run_id=run.id,
        status=run.status,
        total_inserted=inserted,
        total_failed=failed,
    )
