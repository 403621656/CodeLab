import uuid

from pydantic import EmailStr
from sqlmodel import Session, select, func
from typing import Any, Literal

from models import UserCreate, User, UserUpdate, Users, Message
from core.security import get_password_hash


class UserNotFound(Exception):
    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id


class UserAlreadyExists(Exception):
    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id


def get_user_by_id(*, user_id: uuid.UUID, session: Session) -> User | None:
    db_user = session.get(User, user_id)
    return db_user


def get_user_by_ids(*, session: Session, user_ids: list[uuid.UUID]) -> list[User]:
    statement = select(User).where(User.id.in_(user_ids))
    users = session.exec(statement).all()
    return users


def get_user_by_email(*, email: EmailStr, session: Session) -> User | None:
    statement = select(User).where(User.email == email)
    db_user = session.exec(statement).first()
    return db_user


def get_users(
    *,
    session: Session,
    skip: int=0,
    limit: int=100,
    sort_field: str | None =None,
    sort_order: Literal["asc", "desc"]="asc",
    filters: dict[str, tuple[str, Any]] | None=None,
    ) -> Users:
    statement = select(User)
    if filters:
        for field_name, (operator, value) in filters.items():
            if not hasattr(User, field_name):
                continue
            column = getattr(User, field_name)

            if operator == "eq":
                statement = statement.where(column == value)
            elif operator == "ne":
                statement = statement.where(column != value)
            elif operator == "lt":
                statement = statement.where(column < value)
            elif operator == "lte":
                statement = statement.where(column <= value)
            elif operator == "gt":
                statement = statement.where(column > value)
            elif operator == "gte":
                statement = statement.where(column >= value)
            elif operator == "like":
                statement = statement.where(column.ilike(f"%{value}%"))

    count_statement = select(func.count()).select_from(statement)
    count = session.exec(count_statement).one()

    if sort_field and hasattr(User, sort_field):
        column = getattr(User, sort_field)
        if sort_order == "asc":
            statement = statement.order_by(column.asc())
        else:
            statement = statement.order_by(column.desc())

    statement = statement.offset(skip).limit(limit)
    users = session.exec(statement).all()
    return Users(data=users, total=count)


def delete_user(*, user_id: uuid.UUID, session: Session) -> Message:
    user_db = session.get(User, user_id)
    if not user_db:
        raise UserNotFound(user_id)
    session.delete(user_db)
    session.commit()
    return Message(id=user_id)


def create_user(*, user_create: UserCreate, session: Session) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, user_in: UserUpdate, user_id: uuid.UUID, session: Session) -> User:
    db_user = get_user_by_id(user_id=user_id, session=session)
    if not db_user:
        raise UserNotFound(user_id)
    if user_in.email:
        existing_user = get_user_by_email(email=user_in.email, session=session)
        if existing_user and existing_user.id != user_id:
            raise UserAlreadyExists(existing_user.id)
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        extra_data["hashed_password"] = get_password_hash(password)
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.commit()
    session.refresh(db_user)
    return db_user
