const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export interface Tag {
  id: number;
  name: string;
}

export interface ArticleList {
  id: number;
  title: string;
  source_name: string;
  published_at: string | null;
  summary: string | null;
  tags: Tag[];
}

export interface Article extends ArticleList {
  article_url: string;
  status: string;
  created_at: string;
}

export async function fetchArticles(skip = 0, limit = 50): Promise<ArticleList[]> {
  const res = await fetch(`${BASE_URL}/api/articles?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch articles");
  return res.json();
}

export async function fetchArticle(id: number): Promise<Article> {
  const res = await fetch(`${BASE_URL}/api/articles/${id}`);
  if (!res.ok) throw new Error("Failed to fetch article");
  return res.json();
}
