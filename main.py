from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from core.config import settings

app = FastAPI()

bearer = HTTPBearer(auto_error=False)
secret_key = settings.SECRET_KEY

class BearerToken(BaseModel):
    token: str

def require_fixed_token(
        cred: HTTPAuthorizationCredentials|None = Depends(bearer)
):
    if cred is None or cred.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing token")
    if cred.credentials != secret_key:
        raise HTTPException(status_code=403, detail="Invalid token")
    return cred


@app.get("/test-token")
async def test_token(
        cred: HTTPAuthorizationCredentials = Depends(require_fixed_token)
) -> HTTPAuthorizationCredentials:
    return cred

@app.get("/token")
async def get_token() -> BearerToken:
    return BearerToken.model_validate({"token": secret_key})