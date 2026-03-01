"""
Utility functions for logging configuration.
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from config.settings import get_settings


def setup_logging():
    """
    Configure structured logging for the application.
    
    Uses JSON format for production environments and standard format for development.
    """
    settings = get_settings()
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.log_format == "json":
        # JSON formatter for production
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Standard formatter for development
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully")
