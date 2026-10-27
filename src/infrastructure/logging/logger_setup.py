from loguru import logger


def setup_logging():
    logger.add("logs/kalemna_app.log", rotation="50 MB",
               retention = "15 days",
               enqueue = True,
               colorize=True ,
               format = "{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> | {file}:{line} | {message}")

    logger.add('logs/kalemna_error.log', rotation="50 MB",retention="15 days",
                        level="ERROR",
                        serialize=True,
                        backtrace=True,
                        diagnose=True,
                        enqueue=True)
