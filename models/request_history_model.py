#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-22 17:31:15
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""


from datetime import datetime
import hashlib
from pydantic import HttpUrl
from sqlmodel import SQLModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession


class RequestHistoryModel(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    url_hash: str = Field(index=True)
    browser_type: str = Field()
    status_code: int = Field(default=0)
    response_time: float = Field(default=0.0)
    response_size: int = Field(default=0)
    response_headers: str = Field(default="")
    response_body: str = Field(default="")
    request_headers: str = Field(default="")
    request_body: str = Field(default="")
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

    @classmethod
    async def create_request_history(
        cls,
        url: HttpUrl,
        browser_type: str,
        status_code: int,
        response_time: float,
        response_headers: str,
        response_body: str,
        request_headers: str,
        request_body: str,
        session: AsyncSession,
    ):
        """
        create request history
        """
        cls_ins = cls()
        cls_ins.url = str(url)
        cls_ins.url_hash = hashlib.sha256(str(url).encode()).hexdigest()
        cls_ins.browser_type = browser_type
        cls_ins.status_code = status_code
        cls_ins.response_time = response_time
        cls_ins.response_size = len(response_body)
        cls_ins.response_headers = response_headers
        cls_ins.response_body = response_body
        cls_ins.request_headers = request_headers
        cls_ins.request_body = request_body
        cls_ins.created_at = datetime.now()
        cls_ins.updated_at = datetime.now()

        session.add(cls_ins)
        await session.commit()
