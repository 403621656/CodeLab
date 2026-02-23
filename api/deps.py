from sqlmodel import Session
from typing import Annotated, Any
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from collections.abc import Generator

from models import User
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


def parse_filters(params: dict[str, Any]) -> dict[str, tuple[str, Any]]:
    filters = {}
    for key, value in params.items():
        if value is None or value == "":
            continue

        for operator in ["_ne", "_lte", "_lt", "_gte", "_gt", "_like"]:
            if key.endswith(operator):
                field_name = key[: -len(operator)]
                filters[field_name] = (operator[1:], value)
                break

        else:
            if key not in ["_start", "_end", "page", "_per_page", "_sort", "_order", "id"]:
                if hasattr(User, key):
                    filters[key] = ("eq", value)

    return filters
