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
PUBLIC_ARTICLES_URL = os.getenv(
    "PUBLIC_ARTICLES_URL",
    "https://yunhekaku.github.io/ai-news-digest/articles.json",
)
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "30"))
MAX_PER_SOURCE = int(os.getenv("MAX_PER_SOURCE", "4"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

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
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
    },
    {
        "name": "Microsoft AI Blog",
        "url": "https://blogs.microsoft.com/ai/feed/",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
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
    summary_provider: str


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
    remote = load_previous_from_url(PUBLIC_ARTICLES_URL)
    if remote:
        return remote

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


def load_previous_from_url(url: str) -> dict[str, dict[str, Any]]:
    if not url:
        return {}
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return {}
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

    for item in fetched:
        cached = previous.get(item["url"])
        if cached and can_reuse_cached_summary(cached):
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
                    summary_provider=str(cached.get("summary_provider") or "fallback"),
                )
            )
            continue

        text = extract_article_text(item["url"]) or item["rss_summary"] or item["title"]
        result = summarize_with_llm(text, item["title"], item["source"])
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
                summary_provider=result["summary_provider"],
            )
        )

    return articles


def can_reuse_cached_summary(cached: dict[str, Any]) -> bool:
    provider = str(cached.get("summary_provider") or "fallback")
    if LLM_PROVIDER == "none":
        return provider == "fallback"
    return provider == LLM_PROVIDER


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
) -> dict[str, Any]:
    if LLM_PROVIDER == "none":
        return fallback_summary(text, title, source)

    return summarize_with_gemini(text, title, source)


def summarize_with_gemini(text: str, title: str, source: str) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return fallback_summary(text, title, source)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=PROMPT.format(
                title=title,
                source=source,
                text=text[:4000],
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=SUMMARY_SCHEMA,
                temperature=0.2,
                max_output_tokens=700,
            ),
        )
        return normalize_summary(json.loads(response.text), text, title, source, "gemini")
    except Exception as exc:
        print(f"Gemini fallback for {title}: {exc}")
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
  "importance_score": 1から10の整数。今日読む優先度。平均は5〜6。10は業界全体に大きな影響がある記事だけ。
  "reason": "毎日30秒で見る人にとって重要な理由を1文で。",
  "tags": ["最大3個の短いタグ"]
}}

採点ルール:
- 10: 業界全体に大きな影響がある発表、規制、安全性、主要モデルの大幅更新
- 8〜9: 主要企業・主要モデル・開発者体験に明確な影響がある記事
- 6〜7: 今日読む価値はあるが、影響範囲が限定的な記事
- 1〜5: 導入事例、イベント告知、まとめ記事、周辺的な話題
- 全体的に高くしすぎないでください。迷ったら低めにしてください。
"""

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "日本語で2〜3文。事実ベースで短く。",
        },
        "importance_score": {
            "type": "integer",
            "description": "今日読む優先度。平均は5〜6。10は業界全体に大きな影響がある記事だけ。",
            "minimum": 1,
            "maximum": 10,
        },
        "reason": {
            "type": "string",
            "description": "毎日30秒で見る人にとって重要な理由を1文で。",
        },
        "tags": {
            "type": "array",
            "description": "最大3個の短いタグ。",
            "items": {"type": "string"},
            "maxItems": 3,
        },
    },
    "required": ["summary", "importance_score", "reason", "tags"],
    "additionalProperties": False,
}


def normalize_summary(
    data: dict[str, Any],
    text: str,
    title: str,
    source: str,
    provider: str,
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
        "summary_provider": provider,
    }


def fallback_summary(text: str, title: str, source: str) -> dict[str, Any]:
    body = clean_text(text)
    summary = body[:220] if body else title
    return {
        "summary": summary,
        "importance_score": estimate_score(title, body),
        "reason": f"{source} のAI関連ニュースです。",
        "tags": infer_tags(f"{title} {body}"),
        "summary_provider": "fallback",
    }


def estimate_score(title: str, text: str) -> int:
    haystack = f"{title} {text}".lower()
    score = 4
    weighted_keywords = {
        "openai": 1,
        "anthropic": 1,
        "google": 1,
        "agent": 1,
        "model": 1,
        "benchmark": 1,
        "research": 1,
        "security": 2,
        "regulation": 2,
        "safety": 2,
        "frontier": 1,
    }
    for keyword, weight in weighted_keywords.items():
        if keyword in haystack:
            score += weight
    for low_priority in ["event", "podcast", "video", "recap", "quiz", "case study"]:
        if low_priority in haystack:
            score -= 1
    return max(1, min(score, 8))


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
