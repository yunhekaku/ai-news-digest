from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from pydantic_settings import BaseSettings

# backend/app/database.py から2階層上がプロジェクトルート
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    admin_token: str = ""
    supabase_db_url: str = ""
    anthropic_api_key: str = ""
    llm_api_key: str = ""
    gcp_project_id: str = ""
    gcs_bucket_name: str = ""

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


settings = Settings()

# DB URL が未設定のときはローカル SQLite を使う
_db_url = settings.supabase_db_url or "sqlite:///./local.db"
_connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}

engine = create_engine(_db_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
