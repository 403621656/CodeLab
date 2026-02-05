from fastapi import APIRouter

from api.routes import users, token


router = APIRouter()

router.include_router(users.router)
router.include_router(token.router)
