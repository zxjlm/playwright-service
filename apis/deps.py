#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.com
@Create Time: 2025-08-22 16:17:53
@Software: Visual Studio Code
@All Rights Reserved.
"""


from typing import Annotated, AsyncGenerator
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select


def create_session() -> async_sessionmaker[AsyncSession]:
    """
    get session
    """
    from config import engine

    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        close_resets_only=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    get session
    """
    async with async_session() as session:
        yield session


async_session = create_session()
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def verify_auth_key(request: Request, session: SessionDep) -> None:
    """Validate `auth-key` header against AuthConfigModel.

    Raises HTTP 401 if missing/invalid/inactive.
    """
    from models import AuthConfigModel

    from config import service_config
    if service_config.auth_config == 0:
        return None

    auth_key = request.headers.get("auth-key")
    if not auth_key:
        raise HTTPException(status_code=401, detail="Missing auth-key header")

    result = await session.exec(
        select(AuthConfigModel).where(
            AuthConfigModel.api_key == auth_key,
            AuthConfigModel.is_active == True,  # noqa: E712
        )
    )
    record = result.first()
    if not record:
        raise HTTPException(status_code=401, detail="Invalid auth-key")

    return None
