import os
import sys

from loguru import logger as loguru_logger


def init_logger():
    loguru_logger.remove()
    console_logger_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        " - <level>{message}</level>"
    )
    loguru_logger.add(sys.stderr, format=console_logger_format, level="INFO")

    file_logger_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line}"
        " - {message}"
    )
    loguru_logger.add("logs/mcp_server_info.log", rotation="100 MB", format=file_logger_format, level="INFO")
    loguru_logger.add("logs/mcp_server_error.log", rotation="100 MB", format=file_logger_format, level="ERROR")

    if os.getenv("MCP_DEBUG"):
        loguru_logger.add("logs/mcp_server_debug.log", rotation="100 MB", format=file_logger_format, level="DEBUG")
