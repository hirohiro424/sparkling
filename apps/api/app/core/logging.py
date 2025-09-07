from loguru import logger

def setup_logging():
    logger.add("logs/api.log", rotation="10 MB", retention="7 days", serialize=False)
    return logger
