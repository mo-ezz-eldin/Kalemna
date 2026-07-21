from loguru import logger
def setup_logging():
    logger.add('logs/kalemna_app.log',rotation='50 MB',retention='15 days',enqueue=True)
