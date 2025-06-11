"""Main FastAPI application for the Security Compliance Assistant."""
import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.api.routers import ingestion, query, documents

# Create FastAPI application
app = FastAPI(
    title="Security Compliance Assistant API",
    description="API for the Security Compliance Assistant",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")),
    name="static",
)

# Templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"))

# Include routers
app.include_router(ingestion.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/settings")
async def get_settings():
    """Get application settings."""
    return {
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "default_num_results": settings.DEFAULT_NUM_RESULTS,
        "default_min_score": settings.DEFAULT_MIN_SCORE,
        "vector_db_type": settings.VECTOR_DB_TYPE,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_provider": settings.LLM_PROVIDER
    }
