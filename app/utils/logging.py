import logging
from logging.config import dictConfig


def default_logging_config(level: str = "INFO") -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "uvicorn.access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": level,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
        "loggers": {
            "uvicorn.error": {"level": level},
            "uvicorn.access": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
        },
    }


def configure_logging(level: str = "INFO") -> None:
    dictConfig(default_logging_config(level))
    logging.getLogger(__name__).info("Logging configured at %s level", level)
