import uuid

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func
from pydantic import EmailStr


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )


class Users(SQLModel):
    data: list[User]
    total: int


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserPublic(UserBase):
    id: uuid.UUID


class UserCreateResponse(UserBase):
    id: uuid.UUID
    created_at: datetime = Field(serialization_alias="createdAt")


class UserUpdateResponse(UserBase):
    id: uuid.UUID
    updated_at: datetime = Field(serialization_alias="updatedAt")


class UsersPublic(SQLModel):
    data: list[UserPublic]
    total: int


class Message(SQLModel):
    id: uuid.UUID


class BearerToken(SQLModel):
    token: str
