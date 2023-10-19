from typing import ClassVar, Dict

from pydantic import BaseModel

 

class LogConfig(BaseModel):

    """Logging configuration to be set for the server"""

 

    LOGGER_NAME: str = "mycoolapp"

    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"

    LOG_LEVEL: str = "DEBUG"

 

    # Logging config

    version: int = 1

    disable_existing_loggers: bool = False

    formatters: ClassVar[Dict[str, dict]] = {

        "default": {

            "()": "uvicorn.logging.DefaultFormatter",

            "fmt": LOG_FORMAT,

            "datefmt": "%Y-%m-%d %H:%M:%S",

        },

    }

    handlers: ClassVar[Dict[str, dict]] = {

        "default": {

            "formatter": "default",

            "class": "logging.StreamHandler",

            "stream": "ext://sys.stderr",

        },

    }

    loggers: ClassVar[Dict[str, dict]] = {

        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},

    }

 

 

# types of loggers

# -----------------------

# logger.info("Dummy Info")

# logger.error("Dummy Error")

# logger.debug("Dummy Debug")

# logger.warning("Dummy Warning")