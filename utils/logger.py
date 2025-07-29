import logging
from pathlib import Path
import sys

def setup_logger(
    name: str = "BotManager",
    log_file: str = "bot_manager.log",
    log_level: int = logging.INFO,
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    date_format: str = '%Y-%m-%d %H:%M:%S'
) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.
    
    Args:
        name: Logger name (default: 'BotManager')
        log_file: Log file name (default: 'bot_manager.log')
        log_level: Logging level (default: logging.INFO)
        log_format: Log message format
        date_format: Date format in logs
    """
    # Create logs directory if not exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(log_format, datefmt=date_format)

    # File handler
    file_handler = logging.FileHandler(logs_dir / log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger