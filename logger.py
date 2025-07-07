import logging
import os
import sys
from datetime import datetime

def setup_logger(name='mtc_downloader', log_level=logging.INFO):
    """
    Set up and configure a logger for the application.
    
    Args:
        name (str): The name of the logger
        log_level (int): The logging level (default: logging.INFO)
        
    Returns:
        logging.Logger: The configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create file handler for logging to a file
    current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join('logs', f'mtc_downloader_{current_date}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # Create console handler for logging to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log the initialization
    logger.info(f"Logger initialized. Log file: {log_file}")
    
    return logger 