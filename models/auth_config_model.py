#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-11-03 00:00:00
@Software: Visual Studio Code
@Description: Auth config model
All Rights Reserved.
"""

from datetime import datetime
from sqlmodel import SQLModel, Field


class AuthConfigModel(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    source: str = Field(index=True)
    api_key: str = Field(index=True, unique=True)
    description: str | None = Field(default=None)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
