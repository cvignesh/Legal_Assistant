from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.mongo import mongo

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    mongo.connect()
    yield
    # Shutdown
    print("Shutting down...")
    mongo.close()

app = FastAPI(
    title="Legal Assistant API",
    version="1.0.0",
    description="Backend for PDF Parsing, Embedding, and RAG",
    lifespan=lifespan
)

# CORS Config - Allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "db": settings.MONGO_DB}

# Include Routers
from app.api.routes import ingestion, judgments, search, chat
app.include_router(ingestion.router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(judgments.router, prefix="/api/judgments", tags=["Judgments"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])

