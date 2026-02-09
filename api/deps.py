from sqlmodel import Session
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from collections.abc import Generator

from core.db import engine
from core.security import local_token


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


bearer = HTTPBearer(auto_error=False)


def require_fixed_token(
        cred: HTTPAuthorizationCredentials | None = Depends(bearer)
) -> HTTPAuthorizationCredentials:
    if cred is None or cred.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing token")
    if cred.credentials != local_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    return cred


TokenDeps = Annotated[HTTPAuthorizationCredentials, Depends(require_fixed_token)]
SessionDeps = Annotated[Session, Depends(get_db)]
