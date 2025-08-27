#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2025-08-27 10:22:34
@Software: Visual Studio Code
@Copyright: Copyright (c) 2025, harumonia
@Description: ...
All Rights Reserved.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from loguru import logger
from config import service_config

token_auth_scheme = HTTPBearer()


async def verify_bearauth(claims=Depends(token_auth_scheme)) -> bool:
    token = claims.credentials

    if not service_config.mcp_bearer_token:
        return True

    if not token or token != service_config.mcp_bearer_token:
        logger.error(f"Invalid token: {token}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    return True
