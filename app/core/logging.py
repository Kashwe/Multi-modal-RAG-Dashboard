import logging
import sys

def setup_logging():
    """
    Configure application wide logger with formatted console output.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clean previous handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter configuration
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console output handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Suppress verbose dependency loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info("Application logging initialized.")
