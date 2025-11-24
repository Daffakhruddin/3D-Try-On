"""
Logging utilities using loguru.
Provides structured logging with proper formatting.
"""

import sys
from loguru import logger
from typing import Optional


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure the logger with custom formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip"
        )
    
    logger.info(f"Logger initialized with level: {log_level}")


def log_exception(exception: Exception, context: str = "") -> None:
    """
    Log an exception with traceback.
    
    Args:
        exception: The exception to log
        context: Additional context information
    """
    if context:
        logger.exception(f"{context}: {str(exception)}")
    else:
        logger.exception(f"Exception occurred: {str(exception)}")


def log_performance(operation: str, duration_ms: float) -> None:
    """
    Log performance metrics.
    
    Args:
        operation: Name of the operation
        duration_ms: Duration in milliseconds
    """
    logger.debug(f"Performance | {operation}: {duration_ms:.2f}ms")
