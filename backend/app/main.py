from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
import app.models  # noqa: F401 — Base へのモデル登録を確実に行う
from app.routers import articles, admin

# テーブルが存在しなければ作成（ローカル SQLite 用）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI News API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
