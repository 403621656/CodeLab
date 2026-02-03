from fastapi import APIRouter, Depends, HTTPException
from core.security import verify_password, get_password_hash
from models import UserPublic, User, UserCreate, UserRegister, UserUpdate, UserUpdateMe, UsersPublic, UpdatePassword, Message
import crud
from sqlmodel import select, func
import uuid

router = APIRouter(prefix="/users", tags=["users"])

SessionDeps = "pass"
CurrentDeps = "pass"
get_current_active_superuser = "pass"

@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(*, session: SessionDeps, skip: int = 0, limit: int = 100) -> UsersPublic:
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return UsersPublic(count=count, data=users)

@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def create_user(*, user_in: UserCreate, session: SessionDeps) -> UserPublic:
    user = crud.get_user_by_email(user_in.email, session=session)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(user_create=user_in, session=session)
    return user

@router.patch("/me", response_model=UserPublic)
def update_user_me(*, user_in: UserUpdateMe, session: SessionDeps, current_user: CurrentDeps) -> UserPublic:
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@router.patch("/me/password", response_model=Message)
def update_password_me(*, body: UpdatePassword, session: SessionDeps, current_user: CurrentDeps) -> Message:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="New password cannot be the same as the current one")
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password has been changed!")

@router.get("/", response_model=UserPublic)
def read_user_me(current_user: CurrentDeps) -> UserPublic:
    return current_user

@router.delete("/me", response_model=Message)
def delete_user_me(*, session: SessionDeps, current_user: CurrentDeps) -> Message:
    if current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Super users are not allowed to delete themselves")
    session.delete(current_user)
    session.commit()
    return Message(message="User has been deleted!")

@router.post("/signup", response_model=UserPublic)
def register_user(*, session: SessionDeps, user_in: UserRegister) -> UserPublic:
    user = crud.get_user_by_email(user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_create = UserCreate.model_validated(user_in)
    user = crud.create_user(user_create=user_create, session=session)
    return user

@router.get("{user_id}", response_model=UserPublic)
def read_user_by_id(*, session: SessionDeps, user_id: uuid.UUID, current_user: CurrentDeps) -> UserPublic:
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges",)
    return user

@router.patch(
    "user_id",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(*, session: SessionDeps, user_id: uuid.UUID, user_in: UserUpdate) -> UserPublic:
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404,detail="The user with this id does not exist in the system")
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=409, detail="User with this email already exists")
    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user

@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_user(*, session: SessionDeps, user_id: uuid.UUID, current_user: CurrentDeps) -> Message:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(status_code=403, detail="Super users are not allowed to delete themselves")
    session.delete(user)
    session.commit()
    return Message(message="User has been deleted!")

