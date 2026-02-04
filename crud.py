import uuid

from sqlmodel import Session, select, func
from models import UserCreate, User, UserUpdate, Users
from core.security import get_password_hash, verify_password


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



def create_user(*, user_create: UserCreate, session: Session) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, user_update: UserUpdate, db_user:User, session: Session) -> User:
    user_data = user_update.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        extra_data["hashed_password"] = get_password_hash(password)
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, email: str, session: Session) -> User | None:
    statement = select(User).where(User.email == email)
    db_user = session.exec(statement).first()
    return db_user


def get_user_by_id(*, user_id: uuid.UUID, session: Session) -> User | None:
    db_user = session.get(User, user_id)
    return db_user


def authenticate(*, email: str, password: str, session: Session) -> User | None:
    db_user = get_user_by_email(email=email, session=session)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


