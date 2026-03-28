import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchArticle, type Article } from "../api/client";

export default function ArticleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchArticle(Number(id))
      .then(setArticle)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p style={{ padding: 16 }}>読み込み中...</p>;
  if (error) return <p style={{ padding: 16, color: "red" }}>{error}</p>;
  if (!article) return null;

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 16 }}>
      <Link to="/">&larr; 一覧に戻る</Link>
      <h1 style={{ marginTop: 16 }}>{article.title}</h1>
      <div style={{ color: "#666", fontSize: 13 }}>
        {article.source_name}
        {article.published_at && ` · ${new Date(article.published_at).toLocaleDateString("ja-JP")}`}
      </div>
      {article.tags.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {article.tags.map((t) => (
            <span
              key={t.id}
              style={{
                background: "#e8f0fe",
                borderRadius: 4,
                padding: "2px 8px",
                marginRight: 6,
                fontSize: 12,
              }}
            >
              {t.name}
            </span>
          ))}
        </div>
      )}
      {article.summary && (
        <div style={{ marginTop: 24, background: "#f9f9f9", padding: 16, borderRadius: 8 }}>
          <h2 style={{ fontSize: 16, marginTop: 0 }}>要約</h2>
          <p style={{ lineHeight: 1.8 }}>{article.summary}</p>
        </div>
      )}
      <div style={{ marginTop: 24 }}>
        <a href={article.article_url} target="_blank" rel="noopener noreferrer">
          元記事を読む &rarr;
        </a>
      </div>
    </div>
  );
}
