import logging
import os
from pathlib import Path
from datetime import datetime

def setup_logger(name, log_file, level=logging.INFO):
    """
    Configure a logger with a specific name and output file.
    
    Args:
        name: Logger name
        log_file: Log file path
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger
    """
    # Create the log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    Path(log_dir).mkdir(exist_ok=True)
    
    # Configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if not logger.handlers:
        # Create a file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create a formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger