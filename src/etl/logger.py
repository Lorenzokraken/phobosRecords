"""Logging utilities for ETL."""

import logging
import functools
import os

# Crea la directory logs se non esiste
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)


def log_operation(func):
    """Decorator: log function entry/exit and catch exceptions."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.info(f"[START] {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"[OK] {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"[ERROR] {func.__name__} failed: {e}", exc_info=True)
            raise
    return wrapper


def get_logger(name):
    """Get logger instance."""
    return logging.getLogger(name)
