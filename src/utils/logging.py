"""Logging utilities for Archon."""

import logging
import os
from datetime import datetime
from ..config import get_settings


def setup_logging():
    """Set up logging configuration."""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )
    
    # Create logger for Archon
    logger = logging.getLogger('archon')
    logger.info("Archon logging initialized")
    
    return logger
