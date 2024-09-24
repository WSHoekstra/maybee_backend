#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from enum import Enum


class UserType(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_admin: bool = Field(default=False)

    environment_links: List["UserEnvironmentLink"] = Relationship(
        back_populates="user", cascade_delete=True
    )


class UserEnvironmentLink(SQLModel, table=True):
    user_environment_link_id: int | None = Field(default=None, primary_key=True)

    user_id: int | None = Field(default=None, foreign_key="user.user_id")

    environment_id: int | None = Field(
        default=None, foreign_key="environment.environment_id"
    )
    user: User | None = Relationship(back_populates="environment_links")


class UserCreationInput(SQLModel, table=False):
    username: str
    password: str


class UserCreationResponse(SQLModel, table=False):
    user_id: int
    username: str


class Token(SQLModel, table=False):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: Optional[str] = None
