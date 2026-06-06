# AI News Digest

AI関連ニュースを毎日RSSから集めて、30秒で眺めるための静的ニュースダイジェスト。

GitHub Actions が `articles.json` を生成し、GitHub Pages にReactアプリをデプロイする。

## 技術スタック

- Frontend: React + TypeScript + Vite
- Data: `frontend/public/articles.json`
- Batch: GitHub Actions / local Python script
- Hosting: GitHub Pages
- LLM: Anthropic API optional
- Backend: なし
- Database: なし

## ディレクトリ構成

```txt
ai-news-digest/
├── frontend/
│   ├── public/
│   │   └── articles.json
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       └── styles.css
├── scripts/
│   ├── ingest.py
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── pages.yml
└── docs/
    └── architecture.md
```

## 使い方

### ローカルで記事JSONを生成

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/ingest.py
```

`ANTHROPIC_API_KEY` が未設定でも動作する。未設定時はRSS本文や取得本文から短い抜粋を作り、簡易スコアとタグを付ける。

```bash
cp .env.example .env
source .env
python scripts/ingest.py
```

### ローカルで表示

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:3000

公開URL: `https://yunhekaku.github.io/ai-news-digest/`

## GitHub Pages

`.github/workflows/pages.yml` が以下を実行する。

1. RSSからAIニュースを取得
2. `frontend/public/articles.json` を生成
3. Reactアプリをビルド
4. GitHub Pagesへデプロイ

スケジュールは毎日 JST 07:00。手動実行は GitHub Actions の `workflow_dispatch` から行う。

GitHub Pages を使うには、リポジトリの `Settings > Pages` で source を `GitHub Actions` に設定する。

## 環境変数

| 変数名 | 説明 |
|---|---|
| `ANTHROPIC_API_KEY` | 任意。設定すると記事要約、重要度、理由、タグをLLMで生成する |
| `ANTHROPIC_MODEL` | 任意。既定値は `claude-3-5-haiku-latest` |
| `MAX_ITEMS` | 任意。出力する最大記事数。既定値は30 |
| `MAX_PER_SOURCE` | 任意。RSSソースごとの最大取得数。既定値は8 |

## 公開時の方針

- 元記事本文は保存しない
- 保存するのはタイトル、URL、出典、公開日、短い要約、重要度、理由、タグのみ
- APIキーや秘密情報は `articles.json` に入れない
- 一般向けサービスではなく、自分用の軽いニュース棚として運用する
