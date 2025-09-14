import logging
import sys

formatter = logging.Formatter(
    "[%(asctime)s] #%(levelname)-8s %(filename)s: %(lineno)d - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("app.log", encoding="utf-8")

stdout_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.INFO)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)

logger.setLevel(logging.DEBUG)