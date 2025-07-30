from logging import DEBUG, Formatter, getLogger
from logging.handlers import RotatingFileHandler

uvicorn_access = getLogger("uvicorn.access")
uvicorn_access.disabled = True

logger = getLogger("uvicorn")
logger.setLevel(DEBUG)

formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

rotating_handler = RotatingFileHandler("logs.log", maxBytes=5 * 1024 * 1024, backupCount=3)
rotating_handler.setLevel(DEBUG)
rotating_handler.setFormatter(formatter)

logger.addHandler(rotating_handler)
