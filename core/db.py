from sqlmodel import SQLModel, create_engine

from core.config import settings


engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
