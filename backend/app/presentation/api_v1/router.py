from fastapi import APIRouter
from app.presentation.api_v1.endpoints.batch import router as batch_router
from app.presentation.api_v1.endpoints.chat import router as chat_router
from app.presentation.api_v1.endpoints.policy import router as policy_router
from app.presentation.api_v1.endpoints.suppliers import router as suppliers_router
from app.presentation.api_v1.endpoints.contracts import router as contracts_router
from app.presentation.api_v1.endpoints.buyer import router as buyer_router

api_router = APIRouter(prefix="/api")

api_router.include_router(batch_router)
api_router.include_router(chat_router)
api_router.include_router(policy_router)
api_router.include_router(suppliers_router)
api_router.include_router(contracts_router)
api_router.include_router(buyer_router)
