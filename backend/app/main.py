from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import APP_TITLE, APP_VERSION
from app.core.exceptions import DomainException
from app.core.logging import logger
from app.db.seed import seed_database
from app.presentation.api_v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        seed_database()
        logger.info("Database initialized and verified.")
    except Exception as e:
        logger.error(f"Database startup warning: {e}")
    yield

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Automated Policy-Driven PR-to-PO Decision Engine for Corvo Engineering (Clean Architecture & DDD)",
    lifespan=lifespan
)

# Global CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler for Domain Invariant Violations
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(f"Domain exception on {request.url.path}: {exc.message} ({exc.code})")
    return JSONResponse(
        status_code=400,
        content={"status": "error", "code": exc.code, "message": exc.message}
    )


# Mount API Router (/api)
@app.get("/api/health")
def health_check():
    return {
        "app": APP_TITLE,
        "version": APP_VERSION,
        "architecture": "Clean Architecture & Domain-Driven Design (DDD)",
        "status": "healthy",
        "docs_url": "/docs"
    }

app.include_router(api_router)

# Mount frontend production build if available
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def health_check():
        return {
            "app": APP_TITLE,
            "version": APP_VERSION,
            "architecture": "Clean Architecture & Domain-Driven Design (DDD)",
            "status": "healthy",
            "docs_url": "/docs"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
