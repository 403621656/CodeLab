import uuid
import crud

from crud import UserNotFound, UserAlreadyExists
from fastapi import APIRouter, HTTPException

from api.deps import SessionDeps
from models import (
    UserPublic,
    UserCreate,
    UserRegister,
    UserUpdate,
    UsersPublic,
    Message
)


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UsersPublic)
def read_users(*, session: SessionDeps, skip: int = 0, limit: int = 100) -> UsersPublic:
    users = crud.get_users(session=session, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserPublic)
def create_user(*, user_in: UserCreate, session: SessionDeps) -> UserPublic:
    user = crud.get_user_by_email(email=user_in.email, session=session)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(user_create=user_in, session=session)
    return user


@router.post("/signup", response_model=UserPublic)
def register_user(*, session: SessionDeps, user_in: UserRegister) -> UserPublic:
    user = crud.get_user_by_email(email=user_in.email, session=session)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(user_create=user_create, session=session)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(*, session: SessionDeps, user_id: uuid.UUID) -> UserPublic | None:
    user = crud.get_user_by_id(session=session, user_id=user_id)
    return user


@router.patch("/{user_id}",response_model=UserPublic)
def update_user(*, session: SessionDeps, user_id: uuid.UUID, user_in: UserUpdate) -> UserPublic:
    try:
        user = crud.update_user(session=session, user_id=user_id, user_in=user_in)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except UserAlreadyExists:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    return user


@router.delete("/{user_id}", response_model=Message)
def delete_user(*, session: SessionDeps, user_id: uuid.UUID) -> Message:
    try:
        crud.delete_user(session=session, user_id=user_id)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    return Message(message="User has been deleted!")
