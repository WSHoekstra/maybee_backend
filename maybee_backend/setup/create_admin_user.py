#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlmodel import Session, select
from maybee_backend.api.routes import get_password_hash
from maybee_backend.models.user_models import User
from maybee_backend.logging import log


def create_admin_user(username, password, session: Session) -> User:
    sql = select(User).where(User.username == username)
    user = session.exec(sql).first()
    if user:
        log.warning("Admin user already exists")
        return user

    password_hash = get_password_hash(password)
    user = User(
        user_id=1,
        username=username,
        password_hash=password_hash,
        is_admin=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    log.info(f"Created admin user with user_id {user.user_id}")
    return user
