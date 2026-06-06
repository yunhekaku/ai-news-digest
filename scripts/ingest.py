from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "frontend" / "public" / "articles.json"
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "30"))
MAX_PER_SOURCE = int(os.getenv("MAX_PER_SOURCE", "8"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))

RSS_SOURCES = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
    },
    {
        "name": "Anthropic News",
        "url": "https://www.anthropic.com/news/rss",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
    },
]

AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "agent",
    "anthropic",
    "chatgpt",
    "claude",
    "codex",
    "deepmind",
    "gemini",
    "gpt",
    "llm",
    "machine learning",
    "model",
    "openai",
]

EXCLUDED_PATTERNS = [
    "/podcast/",
    "/video/",
    "startup battlefield",
    "get you off your phone",
    "together tech",
]


@dataclass
class Article:
    id: str
    title: str
    url: str
    source: str
    published_at: str | None
    summary: str
    importance_score: int
    reason: str
    tags: list[str]


def main() -> None:
    previous = load_previous()
    fetched = fetch_articles()
    articles = enrich_articles(fetched, previous)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": [asdict(article) for article in articles[:MAX_ITEMS]],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(payload['articles'])} articles to {OUTPUT_PATH}")


def load_previous() -> dict[str, dict[str, Any]]:
    if not OUTPUT_PATH.exists():
        return {}
    try:
        data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {
        article["url"]: article
        for article in data.get("articles", [])
        if isinstance(article, dict) and article.get("url")
    }


def fetch_articles() -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []
    seen: set[str] = set()

    for source in RSS_SOURCES:
        feed = feedparser.parse(source["url"])
        entries = feed.entries[:MAX_PER_SOURCE]
        for entry in entries:
            url = entry.get("link", "").strip()
            title = clean_text(entry.get("title", ""))
            rss_summary = clean_text(entry.get("summary", ""))
            if not url or not title or url in seen:
                continue
            if not is_relevant(title, rss_summary, source["name"], url):
                continue
            seen.add(url)
            articles.append(
                {
                    "id": stable_id(url),
                    "title": title,
                    "url": url,
                    "source": source["name"],
                    "published_at": parse_date(entry),
                    "rss_summary": rss_summary,
                }
            )

    return sorted(
        articles,
        key=lambda article: article.get("published_at") or "",
        reverse=True,
    )


def enrich_articles(
    fetched: list[dict[str, Any]],
    previous: dict[str, dict[str, Any]],
) -> list[Article]:
    articles: list[Article] = []
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    for item in fetched:
        cached = previous.get(item["url"])
        if cached:
            articles.append(
                Article(
                    id=str(cached.get("id") or item["id"]),
                    title=item["title"],
                    url=item["url"],
                    source=item["source"],
                    published_at=item["published_at"],
                    summary=str(cached.get("summary") or item["rss_summary"]),
                    importance_score=int(cached.get("importance_score") or 5),
                    reason=str(cached.get("reason") or "前回生成済みの記事です。"),
                    tags=list(cached.get("tags") or []),
                )
            )
            continue

        text = extract_article_text(item["url"]) or item["rss_summary"] or item["title"]
        result = summarize_with_llm(text, item["title"], item["source"], api_key)
        articles.append(
            Article(
                id=item["id"],
                title=item["title"],
                url=item["url"],
                source=item["source"],
                published_at=item["published_at"],
                summary=result["summary"],
                importance_score=result["importance_score"],
                reason=result["reason"],
                tags=result["tags"],
            )
        )

    return articles


def extract_article_text(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "ai-news-digest/0.1"},
        )
        response.raise_for_status()
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    return clean_text(soup.get_text(" "))[:4000]


def summarize_with_llm(
    text: str,
    title: str,
    source: str,
    api_key: str,
) -> dict[str, Any]:
    if not api_key:
        return fallback_summary(text, title, source)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
            max_tokens=700,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        title=title,
                        source=source,
                        text=text[:4000],
                    ),
                }
            ],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.removeprefix("json").strip()
        return normalize_summary(json.loads(raw), text, title, source)
    except Exception as exc:
        print(f"LLM fallback for {title}: {exc}")
        return fallback_summary(text, title, source)


PROMPT = """\
次のAIニュース記事を、日本語で短く整理してください。回答はJSONのみ。

title: {title}
source: {source}

本文:
{text}

形式:
{{
  "summary": "日本語で2〜3文。事実ベースで短く。",
  "importance_score": 1から10の整数,
  "reason": "毎日30秒で見る人にとって重要な理由を1文で。",
  "tags": ["最大3個の短いタグ"]
}}
"""


def normalize_summary(
    data: dict[str, Any],
    text: str,
    title: str,
    source: str,
) -> dict[str, Any]:
    fallback = fallback_summary(text, title, source)
    summary = clean_text(str(data.get("summary") or fallback["summary"]))
    reason = clean_text(str(data.get("reason") or fallback["reason"]))
    tags = data.get("tags") if isinstance(data.get("tags"), list) else fallback["tags"]
    return {
        "summary": summary[:500],
        "importance_score": clamp_score(data.get("importance_score", 5)),
        "reason": reason[:240],
        "tags": [clean_text(str(tag))[:24] for tag in tags[:3] if clean_text(str(tag))],
    }


def fallback_summary(text: str, title: str, source: str) -> dict[str, Any]:
    body = clean_text(text)
    summary = body[:220] if body else title
    return {
        "summary": summary,
        "importance_score": estimate_score(title, body),
        "reason": f"{source} のAI関連ニュースです。",
        "tags": infer_tags(f"{title} {body}"),
    }


def estimate_score(title: str, text: str) -> int:
    haystack = f"{title} {text}".lower()
    score = 5
    for keyword in [
        "openai",
        "anthropic",
        "google",
        "agent",
        "model",
        "benchmark",
        "research",
        "security",
        "regulation",
    ]:
        if keyword in haystack:
            score += 1
    return min(score, 9)


def infer_tags(text: str) -> list[str]:
    rules = [
        ("OpenAI", "openai"),
        ("Anthropic", "anthropic"),
        ("Google", "google"),
        ("Agent", "agent"),
        ("Model", "model"),
        ("Research", "research"),
        ("Policy", "regulation"),
        ("Security", "security"),
        ("OSS", "open source"),
    ]
    lower = text.lower()
    tags = [label for label, keyword in rules if keyword in lower]
    return tags[:3] or ["AI"]


def is_relevant(title: str, summary: str, source: str, url: str) -> bool:
    lower_url = url.lower()
    lower_title = title.lower()
    if any(pattern in lower_url or pattern in lower_title for pattern in EXCLUDED_PATTERNS):
        return False
    if source in {"OpenAI News", "Anthropic News"}:
        return True
    haystack = f"{title} {summary}".lower()
    return any(keyword in haystack for keyword in AI_KEYWORDS)


def parse_date(entry: Any) -> str | None:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, IndexError):
            pass

    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
    return None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", BeautifulSoup(value or "", "html.parser").get_text(" ")).strip()


def stable_id(url: str) -> str:
    import hashlib

    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def clamp_score(value: Any) -> int:
    try:
        return max(1, min(10, int(value)))
    except (TypeError, ValueError):
        return 5


if __name__ == "__main__":
    main()
