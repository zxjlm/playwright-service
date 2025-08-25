#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 16:17:53
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""


from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession


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
