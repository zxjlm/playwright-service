#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2026-01-13 17:35:39
@Software: Visual Studio Code
@Copyright: Copyright (c) 2026, harumonia
@Description: ...
All Rights Reserved.
"""
import logging
import os
from pprint import pformat
from typing import Any
import sys
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from loguru._defaults import LOGURU_FORMAT
from loguru import logger


def get_otlp_handler(endpoint: str, service_name: str, env: str) -> logging.Handler:
    """
    Setup OpenTelemetry logging and return a logging handler.
    """
    # Create Resource (service identification)
    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": env,
        }
    )

    # Create LoggerProvider
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)

    # Create OTLP Log Exporter
    # Use insecure=True for internal gRPC endpoints usually
    otlp_exporter = OTLPLogExporter(
        endpoint=endpoint,
        insecure=True,
    )

    # Add BatchLogRecordProcessor
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

    # Create logging handler
    handler = LoggingHandler(
        level=logging.DEBUG,
        logger_provider=logger_provider,
    )

    return handler


def format_record(record: dict) -> str:
    """
    loguru format record
    use pformat to format payload data, for debugging to view request/response body.
    """

    format_string = LOGURU_FORMAT
    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"], indent=4, compact=True, width=88
        )
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"
    return format_string


def setup_otlp_logger(endpoint: str, service_name: str, env: str) -> None:
    """
    Setup OpenTelemetry logging and return a logging handler.
    """
    sinks: list[dict[str, Any]] = [
        {"sink": sys.stdout, "level": logging.INFO, "format": format_record}
    ]
    try:
        handler = get_otlp_handler(endpoint, service_name, env)
        sinks.append({"sink": handler, "level": logging.INFO})
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry logging: {e}")
    finally:
        logger.configure(handlers=sinks)
