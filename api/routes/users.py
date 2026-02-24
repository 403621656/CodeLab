import uuid
import crud

from fastapi import APIRouter, HTTPException, Query, Request
from typing import Literal, Annotated

from api.deps import SessionDeps, parse_filters
from crud import UserNotFound, UserAlreadyExists
from models import (
    UserPublic,
    UserCreate,
    UserCreateResponse,
    UserRegister,
    UserUpdate,
    UserUpdateResponse,
    UsersPublic,
    Message,
)


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UsersPublic)
def read_users(
        *,
        session: SessionDeps,
        request: Request,
        _start: Annotated[int | None , Query(ge=0)] = None,
        _end: Annotated[int | None, Query(ge=1)] = None,
        page: Annotated[int | None, Query(ge=1)] = None,
        _per_page: Annotated[int | None, Query(ge=1, le=100)] = None,
        _sort: Annotated[str | None, Query()] = None,
        _order: Annotated[Literal["asc", "desc"], Query()] = "asc",
        id: Annotated[str | None, Query()] = None,
) -> UsersPublic:
    all_params = dict(request.query_params)

    for key in ["_start", "_end", "page", "_per_page", "_sort", "_order", "id"]:
        all_params.pop(key, None)

    if id:
        user_ids = [uuid.UUID(uid.strip()) for uid in id.split(",")]
        users = crud.get_user_by_ids(session=session, user_ids=user_ids)
        return UsersPublic(data=users, total=len(users))

    if _start is not  None and _end is not None:
        skip = _start
        limit = _end - _start
    elif page is not None and _per_page is not None:
        skip = (page - 1) * _per_page
        limit = _per_page

    filters = parse_filters(all_params)

    users = crud.get_users(
        session=session,
        skip=skip,
        limit=limit,
        sort_field=_sort,
        sort_order=_order,
        filters=filters,
    )

    return UsersPublic(data=users.data, total=users.total)


@router.post("/", response_model=UserCreateResponse)
def create_user(*, user_in: UserCreate, session: SessionDeps) -> UserCreateResponse:
    user = crud.get_user_by_email(email=user_in.email, session=session)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(user_create=user_in, session=session)
    return user


@router.post("/signup", response_model=UserCreateResponse)
def register_user(*, session: SessionDeps, user_in: UserRegister) -> UserCreateResponse:
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


@router.patch("/{user_id}",response_model=UserUpdateResponse)
def update_user(*, session: SessionDeps, user_id: uuid.UUID, user_in: UserUpdate) -> UserUpdateResponse:
    try:
        user = crud.update_user(session=session, user_id=user_id, user_in=user_in)
        return user
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except UserAlreadyExists:
        raise HTTPException(status_code=409, detail="User with this email already exists")


@router.delete("/{user_id}", response_model=Message)
def delete_user(*, session: SessionDeps, user_id: uuid.UUID) -> Message:
    try:
        result = crud.delete_user(session=session, user_id=user_id)
        return result
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
