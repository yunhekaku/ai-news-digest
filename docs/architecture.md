# Architecture

## 概要

AI News Digest は、AI関連ニュースをRSSから取得して静的JSONに変換し、GitHub Pagesで表示する個人用ダイジェスト。

主目的は「毎日30秒でAIニュースの流れを見る」こと。バックエンド、DB、常時稼働サーバーは持たない。

## スコープ

### 実装する

- RSSからAI関連ニュースを取得
- URLベースで重複排除
- 記事タイトル、URL、出典、公開日を保存
- 短い要約、読む優先度、理由、タグを保存
- 重要度順/新着順で表示
- GitHub Actionsで毎日更新
- GitHub Pagesで公開

### 実装しない

- ユーザー認証
- DB
- APIサーバー
- Cloud Run / Cloud Storage
- 課金
- 通知
- 元記事全文の保存

## データフロー

```txt
GitHub Actions
  └─ python scripts/ingest.py
       ├─ RSS feeds
       ├─ optional Gemini API
       └─ frontend/public/articles.json
            └─ Vite build
                 └─ GitHub Pages
```

## データモデル

`frontend/public/articles.json`

```json
{
  "generated_at": "2026-06-06T22:00:00+00:00",
  "articles": [
    {
      "id": "stable-hash",
      "title": "Article title",
      "url": "https://example.com/article",
      "source": "Source name",
      "published_at": "2026-06-06T00:00:00+00:00",
      "summary": "短い要約",
      "importance_score": 8,
      "reason": "重要な理由",
      "tags": ["OpenAI", "Model"],
      "summary_provider": "gemini"
    }
  ]
}
```

## RSSソース

初期ソースは `scripts/ingest.py` の `RSS_SOURCES` で管理する。

- TechCrunch AI
- OpenAI News
- Anthropic News
- Google AI Blog

## LLM動作

`GEMINI_API_KEY` がある場合は、記事本文またはRSS本文から以下をJSONで生成する。

- `summary`
- `importance_score`
- `reason`
- `tags`

未設定の場合は、本文抜粋、簡易スコア、キーワードタグでフォールバックする。

既存の `articles.json` はキャッシュとして使う。ただし `summary_provider` が現在の `LLM_PROVIDER` と一致しない場合は再生成する。
