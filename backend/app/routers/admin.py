import logging
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
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


def verify_token(authorization: str = Header(default="")):
    """ADMIN_TOKEN が設定されているときのみ検証する。未設定はローカル開発用として許可。"""
    if not settings.admin_token:
        return
    expected = f"Bearer {settings.admin_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


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


def _run_ingest(run_id: int):
    """バックグラウンドで実行される本体。DB セッションを独立して取得する。"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
        inserted = 0
        failed = 0

        for raw in fetch_articles_from_feeds():
            if not raw["article_url"]:
                failed += 1
                continue
            if db.query(Article).filter(Article.article_url == raw["article_url"]).first():
                continue
            try:
                text = extract_text(raw["article_url"])
                summary = summarize(text)
                pub = datetime(*raw["published_at"][:6]) if raw["published_at"] else None
                db.add(Article(
                    source_name=raw["source_name"],
                    article_url=raw["article_url"],
                    title=raw["title"],
                    published_at=pub,
                    summary=summary,
                    status="summarized" if summary else "pending",
                ))
                db.commit()
                inserted += 1
            except Exception as e:
                logger.error(f"Failed to process {raw['article_url']}: {e}")
                failed += 1

        run.status = "completed"
        run.total_inserted = inserted
        run.total_failed = failed
        db.commit()
        logger.info(f"Ingest run {run_id} completed: inserted={inserted} failed={failed}")
    except Exception as e:
        logger.error(f"Ingest run {run_id} failed: {e}")
        if run:
            run.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/ingest", response_model=IngestResponse, status_code=202)
def ingest(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
):
    run = IngestionRun(started_at=datetime.utcnow(), status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(_run_ingest, run.id)

    return IngestResponse(
        run_id=run.id,
        status=run.status,
        total_inserted=0,
        total_failed=0,
    )
