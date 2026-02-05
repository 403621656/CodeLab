from sqlmodel import Session
from typing import Annotated
from fastapi import Depends
from collections.abc import Generator

from core.db import engine


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDeps = Annotated[Session, Depends(get_db)]