"""IDA-MAS — Intelligent Document Analysis Multi-Agent System (MVP).

FastAPI entry point. Serves the API and static frontend.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.utils.logger import setup_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
setup_logging()

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="IDA-MAS",
    description="Intelligent Document Analysis Multi-Agent System",
    version="0.1.0",
)

# CORS — allow frontend dev access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Ensure data directories exist
# ---------------------------------------------------------------------------
for p in [settings.UPLOAD_DIR, settings.CHROMA_DIR]:
    Path(p).mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Health check (before routers & static mount)
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# ---------------------------------------------------------------------------
# Register API routers
# ---------------------------------------------------------------------------
from backend.api.chat import router as chat_router
from backend.api.upload import router as upload_router
from backend.api.documents import router as documents_router

app.include_router(chat_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(documents_router, prefix="/api")

# ---------------------------------------------------------------------------
# Serve static frontend — mounted at /api ends with a catch-all at /
# ---------------------------------------------------------------------------
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)

# Mount static files at /, but FastAPI checks explicit routes first
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
