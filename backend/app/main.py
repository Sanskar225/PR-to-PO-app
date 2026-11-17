import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import APP_TITLE, APP_VERSION
from app.api.routes_pr import router as pr_router
from app.api.routes_policy import router as policy_router
from app.api.routes_suppliers import router as suppliers_router
from app.api.routes_contracts import router as contracts_router
from app.api.routes_buyer import router as buyer_router
from app.db.seed import seed_database

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Automated Policy-Driven PR-to-PO Decision Engine for Corvo Engineering"
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup hook to guarantee database is seeded
@app.on_event("startup")
def on_startup():
    try:
        seed_database()
        print("Database initialized and verified.")
    except Exception as e:
        print(f"Database startup warning: {e}")

# Include Routers
app.include_router(pr_router)
app.include_router(policy_router)
app.include_router(suppliers_router)
app.include_router(contracts_router)
app.include_router(buyer_router)

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
            "status": "healthy",
            "docs_url": "/docs"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
