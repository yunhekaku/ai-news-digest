# AI News App

AI関連ニュースを定期収集し、LLMで日本語要約・タグ付けして閲覧できる個人用Webアプリ。

## 技術スタック

- **Frontend**: React + TypeScript (Vite)
- **Backend**: FastAPI
- **Database**: Supabase Postgres
- **Storage**: Cloud Storage (GCP)
- **Hosting**: Cloud Run
- **CI/CD**: GitHub Actions

## ディレクトリ構成

```
ai-news-app/
├── frontend/          # React + TypeScript (Vite)
│   ├── src/
│   │   ├── api/       # API クライアント
│   │   ├── pages/     # ArticleList, ArticleDetail
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   └── nginx.conf
├── backend/           # FastAPI
│   ├── app/
│   │   ├── main.py    # エントリポイント
│   │   ├── database.py
│   │   ├── models.py  # SQLAlchemy モデル
│   │   ├── schemas.py # Pydantic スキーマ
│   │   └── routers/
│   │       ├── articles.py  # GET /api/articles
│   │       └── admin.py     # POST /api/admin/ingest
│   ├── requirements.txt
│   └── Dockerfile
├── .github/
│   └── workflows/
│       └── ingest.yml  # 定期収集バッチ
├── docs/
│   └── architecture.md
├── docker-compose.yml
└── .env.example
```

## セットアップ

### 1. 環境変数

```bash
cp .env.example .env
# .env を編集して各値を設定
```

| 変数名 | 説明 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API キー（要約に使用） |
| `SUPABASE_DB_URL` | Supabase の PostgreSQL 接続文字列 |
| `GCP_PROJECT_ID` | GCP プロジェクト ID |
| `GCS_BUCKET_NAME` | Cloud Storage バケット名 |
| `VITE_API_BASE_URL` | フロントエンドから見た API の URL |

### 2. ローカル起動（Docker）

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000
- API docs: http://localhost:8000/docs

### 3. ローカル起動（個別）

**Backend**

`SUPABASE_DB_URL` が未設定の場合、SQLite (`backend/local.db`) で自動起動します。

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ヘルスチェック: `curl http://localhost:8000/health`

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

## API

| Method | Path | 説明 |
|---|---|---|
| GET | `/health` | ヘルスチェック |
| GET | `/api/articles` | 記事一覧 |
| GET | `/api/articles/{id}` | 記事詳細 |
| POST | `/api/admin/ingest` | 手動収集実行 |

## バッチ処理

GitHub Actions (`ingest.yml`) が毎日 JST 10:00 に `/api/admin/ingest` を呼び出す。
手動実行も GitHub Actions の `workflow_dispatch` から可能。

手動で API を叩く場合:
```bash
curl -X POST http://localhost:8000/api/admin/ingest
```
