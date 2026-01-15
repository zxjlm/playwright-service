#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2026-01-13 18:18:34
@Software: Visual Studio Code
@Copyright: Copyright (c) 2026, harumonia
@Description: ...
All Rights Reserved.
"""
import time
import typing
import uuid

from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
import json

from loguru import logger


def truncate_dict_strings(
    data: typing.Union[dict, list], max_len: int = 20
) -> typing.Union[dict, list]:
    """
    truncate dict strings in k-v where v is string type and length is greater than max_len
    """

    def truncate_one(item):
        if isinstance(item, dict):
            return {
                k: (
                    truncate_one(v)
                    if isinstance(v, (dict, list))
                    else (
                        v[:max_len] + "..."
                        if isinstance(v, str) and len(v) > max_len
                        else v
                    )
                )
                for k, v in item.items()
            }
        elif isinstance(item, list):
            return [truncate_one(i) for i in item]
        else:
            return item

    try:
        return truncate_one(data)
    except Exception as e:
        logger.error(
            f"================ failed to truncate dict strings. data: {data}, error: {e}"
        )
        return data


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """middleware: record request url, headers, params, body, duration, and trace_id"""

    _filter_endpoints = ["/metrics", "/health"]

    async def dispatch(self, request: Request, call_next):
        # generate trace_id, use trace_id in request header for cross-service tracing
        trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())

        start_time = time.perf_counter()

        # get url path and normalize it (remove trailing slash)
        path = request.url.path.rstrip("/")
        if not path:  # handle root path "/"
            path = "/"

        # check if normalized path matches any filtered endpoint exactly
        if path in self._filter_endpoints:
            return await call_next(request)

        # get full url for logging
        url = str(request.url)

        # get and truncate headers
        headers = dict(request.headers)
        truncated_headers = truncate_dict_strings(headers, max_len=128)
        if "authtoken" in truncated_headers:
            truncated_headers.pop("authtoken")

        # get and truncate query params
        params = dict(request.query_params)
        truncated_params = truncate_dict_strings(params, max_len=128)

        # get and truncate body
        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        body = json.loads(body_bytes.decode("utf-8"))
                        body = truncate_dict_strings(body, max_len=128)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # non-json body, truncate to string
                        body_str = body_bytes.decode("utf-8", errors="replace")
                        body = (
                            body_str[:128] + "..." if len(body_str) > 128 else body_str
                        )
            except Exception as e:
                logger.warning(f"Failed to read request body: {e}")

        user_email = "uo"
        if "user" in request.scope:
            user = request.scope["user"]
            user_email = getattr(user, "email", "uo-email")

        # use contextualize to bind trace_id, all logs in this context will automatically have trace_id
        with logger.contextualize(trace_id=trace_id):
            response = await call_next(request)

            # calculate request duration (milliseconds)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # get matching route template for statistics (e.g. /{log_id}/submit instead of /1/submit)
            route = request.scope.get("route")
            route_path = route.path if route else request.url.path

            # record request information
            logger.bind(
                **{
                    "route": route_path,
                    "headers": truncated_headers,
                    "params": truncated_params,
                    "body": body,
                    "user": user_email,
                    "duration_ms": round(duration_ms, 2),
                    "status_code": response.status_code,
                }
            ).info(
                f"Request: url={url}",
            )

            return response
