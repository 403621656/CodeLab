import uuid

from pydantic import EmailStr
from sqlmodel import Session, select, func

from models import UserCreate, User, UserUpdate, Users
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


def get_user_by_email(*, email: EmailStr, session: Session) -> User | None:
    statement = select(User).where(User.email == email)
    db_user = session.exec(statement).first()
    return db_user


def get_users(
    *,
    session: Session,
    skip: int=0,
    limit: int=100,
    ) -> Users:
    statement_count = select(func.count()).select_from(User)
    count = session.exec(statement_count).one()
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return Users(data=users, count=count)


def delete_user(*, user_id: uuid.UUID, session: Session) -> None:
    user_db = session.get(User, user_id)
    if not user_db:
        raise UserNotFound(user_id)
    session.delete(user_db)
    session.commit()


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




