from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_db_url: str = ""
    anthropic_api_key: str = ""
    llm_api_key: str = ""
    gcp_project_id: str = ""
    gcs_bucket_name: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

engine = create_engine(settings.supabase_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
