import logging
import sys

def setup_logging():
    formatter = logging.Formatter(
        "[%(asctime)s] #%(levelname)-8s %(filename)s: %(lineno)d - %(name)s - %(message)s"
    )



    stdout_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler("/minibanking/logs/app.log", encoding="utf-8")

    stdout_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.INFO)

    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)


    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(file_handler)

    return root_logger

logger = setup_logging()