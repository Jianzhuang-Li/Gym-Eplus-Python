import logging
import sys
from .constant import LOG_FORMAT, LOG_LEVEL_MODEL_JSON
from typing import Any, Dict, Optional, Tuple, Union

class CustomFormatter(logging.Formatter):
    """Custom logger format for terminal messages"""
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = LOG_FORMAT

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Logger():
    """Sinergym terminal logger for simulation executions.
    """

    def getLogger(
            self,
            name: str,
            level: str,
            formatter: Any = CustomFormatter()) -> logging.Logger:
        """Return Sinergym logger for the progress output in terminal.

        Args:
            name (str): logger name
            level (str): logger level
            formatter (Callable): logger formatter class

        Returns:
            logging.logger

        """
        logger = logging.getLogger(name)
        consoleHandler = logging.StreamHandler(stream=sys.stdout)
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)
        logger.setLevel(level)
        logger.propagate = False
        return logger
    
if __name__ == "__main__":
    logger = Logger().getLogger("test_logger", LOG_LEVEL_MODEL_JSON)
    logger.info("test_message.")
    logger.warning("warning message.")
    