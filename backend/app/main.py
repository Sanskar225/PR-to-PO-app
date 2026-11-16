from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import APP_TITLE, APP_VERSION
from app.api.routes_pr import router as pr_router
from app.api.routes_policy import router as policy_router
from app.api.routes_suppliers import router as suppliers_router
from app.api.routes_contracts import router as contracts_router
from app.api.routes_buyer import router as buyer_router

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

# Include Routers
app.include_router(pr_router)
app.include_router(policy_router)
app.include_router(suppliers_router)
app.include_router(contracts_router)
app.include_router(buyer_router)

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
