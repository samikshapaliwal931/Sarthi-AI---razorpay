from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.merchant import router as merchant_router
from app.api.v1.products import router as products_router
from app.api.v1.orders import router as orders_router
from app.api.v1.customers import router as customers_router
from app.api.v1.carts import router as carts_router
from app.api.v1.payments import router as payments_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.policies import router as policies_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.ai import router as ai_router
from app.api.v1.storefront import router as storefront_router
from app.api.v1.agent_activity import router as agent_activity_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.ai_buyer import router as ai_buyer_router
from app.api.v1.recovery import router as recovery_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(merchant_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
api_router.include_router(customers_router)
api_router.include_router(carts_router)
api_router.include_router(payments_router)
api_router.include_router(recommendations_router)
api_router.include_router(opportunities_router)
api_router.include_router(policies_router)
api_router.include_router(analytics_router)
api_router.include_router(ai_router)
api_router.include_router(storefront_router)
api_router.include_router(agent_activity_router)
api_router.include_router(campaigns_router)
api_router.include_router(experiments_router)
api_router.include_router(integrations_router)
api_router.include_router(ai_buyer_router)
api_router.include_router(recovery_router)
