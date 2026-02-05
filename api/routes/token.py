from fastapi import APIRouter
from fastapi.security import HTTPAuthorizationCredentials

from models import BearerToken
from core.security import local_token
from api.deps import TokenDeps

router = APIRouter(prefix="/token", tags=["Token"])


@router.get("/", response_model=BearerToken)
async def read_token() -> BearerToken:
    return BearerToken(token=local_token)


@router.get("/test-token", response_model=HTTPAuthorizationCredentials)
async def test_token(cred: TokenDeps) -> HTTPAuthorizationCredentials:
    return cred