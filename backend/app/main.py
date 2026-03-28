from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import articles, admin

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
