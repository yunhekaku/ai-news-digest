import { useEffect, useMemo, useState } from "react";
import "./styles.css";

type Article = {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  summary: string;
  importance_score: number;
  reason: string;
  tags: string[];
  summary_provider: string;
};

type Digest = {
  generated_at: string | null;
  articles: Article[];
};

type SortMode = "date" | "score";

export default function App() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("score");

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}articles.json`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("articles.json を読み込めませんでした");
        }
        return response.json();
      })
      .then(setDigest)
      .catch((err) => setError(err.message));
  }, []);

  const articles = useMemo(() => {
    const items = [...(digest?.articles ?? [])];
    return items.sort((a, b) => {
      if (sortMode === "score") {
        return (
          b.importance_score - a.importance_score ||
          dateValue(b.published_at) - dateValue(a.published_at)
        );
      }
      return dateValue(b.published_at) - dateValue(a.published_at);
    });
  }, [digest, sortMode]);

  const topStories = articles.slice(0, 3);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="kicker">Daily AI Notes</p>
          <h1>AI News Digest</h1>
        </div>
        <div className="generated">
          <span>Updated</span>
          <time>{formatDateTime(digest?.generated_at)}</time>
        </div>
      </header>

      <section className="summary-band" aria-label="Top stories">
        {topStories.length > 0 ? (
          topStories.map((article) => (
            <a className="top-story" href={article.url} key={article.id} target="_blank" rel="noreferrer">
              <span className="score">{article.importance_score}</span>
              <span>{article.title}</span>
            </a>
          ))
        ) : (
          <p className="empty">まだ記事がありません。GitHub Actionsか `python scripts/ingest.py` で更新します。</p>
        )}
      </section>

      <div className="controls" aria-label="Sort articles">
        <button className={sortMode === "score" ? "active" : ""} onClick={() => setSortMode("score")}>
          重要度順
        </button>
        <button className={sortMode === "date" ? "active" : ""} onClick={() => setSortMode("date")}>
          新着順
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="article-list" aria-label="Articles">
        {articles.map((article) => (
          <article className="article" key={article.id}>
            <div className="article-score" aria-label={`Importance ${article.importance_score}`}>
              {article.importance_score}
            </div>
            <div className="article-body">
              <div className="meta">
                <span>{article.source}</span>
                <span>{formatDate(article.published_at)}</span>
              </div>
              <h2>
                <a href={article.url} target="_blank" rel="noreferrer">
                  {article.title}
                </a>
              </h2>
              <p className="summary">{article.summary}</p>
              <p className="reason">{article.reason}</p>
              <div className="tags">
                {article.tags.map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

function dateValue(value: string | null) {
  return value ? new Date(value).getTime() : 0;
}

function formatDate(value: string | null) {
  if (!value) return "日付なし";
  return new Intl.DateTimeFormat("ja-JP", {
    month: "numeric",
    day: "numeric",
  }).format(new Date(value));
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "未生成";
  return new Intl.DateTimeFormat("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
