import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchArticles, type ArticleList } from "../api/client";

export default function ArticleListPage() {
  const [articles, setArticles] = useState<ArticleList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchArticles()
      .then(setArticles)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ padding: 16 }}>読み込み中...</p>;

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 16 }}>
      <h1>AI ニュース</h1>
      {error && (
        <p style={{ color: "#999", background: "#f5f5f5", padding: 12, borderRadius: 6, fontSize: 14 }}>
          バックエンドに接続できません。<code>uvicorn app.main:app --reload</code> を起動してください。
        </p>
      )}
      {!error && articles.length === 0 && <p>記事がありません。</p>}
      <ul style={{ listStyle: "none", padding: 0 }}>
        {articles.map((a) => (
          <li key={a.id} style={{ borderBottom: "1px solid #eee", padding: "16px 0" }}>
            <Link to={`/articles/${a.id}`} style={{ fontWeight: "bold", fontSize: 18 }}>
              {a.title}
            </Link>
            <div style={{ color: "#666", fontSize: 13, marginTop: 4 }}>
              {a.source_name}
              {a.published_at && ` · ${new Date(a.published_at).toLocaleDateString("ja-JP")}`}
            </div>
            {a.summary && <p style={{ marginTop: 8 }}>{a.summary}</p>}
            {a.tags.length > 0 && (
              <div style={{ marginTop: 8 }}>
                {a.tags.map((t) => (
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
          </li>
        ))}
      </ul>
    </div>
  );
}
