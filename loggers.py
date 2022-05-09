import logging.config
import os
import sys
from logging import Logger, PercentStyle
from multiprocessing import Queue
from time import sleep
from typing import Dict, List, Text

from yaml import safe_load

CRITICAL_LOGGER = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "NOTSET",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "error": {
            "level": "CRITICAL",
            "propagate": False,
            "handlers": ["console"]
        }
    },
    "root": {
        "level": "NOTSET",
        "propagate": False,
        "handlers": ["console"],
    },
    "formatters": {
        "standard": {
            "format": f"%(asctime)s, %(levelname)s: %(message)s,"
                      f"current directory: "
                      f"{os.path.dirname(os.path.abspath(__file__))}",
            "datefmt": "%d-%m-%Y %I:%M:%S %p",
            "style": "%",
            "class": "logging.Formatter"
        }
    }
}

COLORS = {
    "grey": "\x1b[1;98;20m",
    "green": "\x1b[92;20m",
    "yellow": "\x1b[33;20m",
    "red": "\x1b[31;20m",
    "bold_red": "\x1b[31;1m",
    "reset": "\x1b[0m"
}


class CustomFormatter(logging.Formatter):

    def __init__(self, fmt: Text, datefmt: Text,
                 style: PercentStyle, color: Text = True):
        super(CustomFormatter, self).__init__()
        self._color = color
        if self._color is True:
            self._formats = {
                logging.DEBUG: COLORS["grey"] + fmt + COLORS["reset"],
                logging.INFO: COLORS["green"] + fmt + COLORS["reset"],
                logging.WARNING: COLORS["yellow"] + fmt + COLORS["reset"],
                logging.ERROR: COLORS["red"] + fmt + COLORS["reset"],
                logging.CRITICAL: COLORS["bold_red"] + fmt + COLORS["reset"]
            }
        else:
            self._formats = {
                logging.DEBUG: fmt,
                logging.INFO: fmt,
                logging.WARNING: fmt,
                logging.ERROR: fmt,
                logging.CRITICAL: fmt
            }
        self._datefmt = datefmt
        self._style: PercentStyle = style

    def format(self, record):
        log_fmt = self._formats.get(record.levelno)
        formatter = logging.Formatter(fmt=log_fmt, datefmt=self._datefmt,
                                      style=self._style)
        return formatter.format(record)


class CustomFilter(logging.Filter):
    def __init__(self, param=None):
        super().__init__()
        self.param = param

    def filter(self, record):
        _allow = False
        if self.param is None:
            _allow = True
        elif record.name == "root":
            for lvl in self.param.keys():
                if record.levelno == self.param[lvl]:
                    _allow = True
        else:
            if self.param[record.name.upper()] == record.levelno:
                _allow = True
        # if _allow:
        #record.msg = "changed: " + record.msg
        return _allow


def queue_handler_setup(q: Queue) -> Logger:
    _queue_handler = logging.handlers.QueueHandler(q)
    _basic_logger = logging.getLogger()
    _basic_logger.setLevel(0)
    _basic_logger.propagate = False
    _basic_logger.addHandler(_queue_handler)
    return _basic_logger


def queue_listener(q: Queue):
    while True:
        while not q.empty():
            record = q.get()
            if record is not None and record.name != "root":
                logger: Logger = logging.getLogger(record.name)
                logger.handle(record)
            elif record is not None and record.name == "root":
                logger: Logger = logging.getLogger()
                logger.handle(record)
            else:
                sys.exit(0)
        sleep(1)


def listener_setup(q: Queue = None):
    load_config()
    queue_listener(q)


def load_config():
    try:
        if os.path.exists("log_settings.yaml"):
            with open("log_settings.yaml", encoding="utf8") as file:
                log_cfg: Dict = safe_load(file)
            logging.config.dictConfig(log_cfg)
        else:
            msg = "File log_settings.yaml not found!"
            raise FileNotFoundError(msg)
    except FileNotFoundError as err:
        logging.config.dictConfig(CRITICAL_LOGGER)
        _basic_logger: Logger = logging.getLogger("error")
        _basic_logger.critical(err)


def logger_generator() -> List[Logger]:
    _logger_names = ["critical", "error", "warning", "info_b_con", "info_h_con",
                     "info_file", "debug"]

    for x in _logger_names:
        if logging.root.manager.loggerDict.get(x):
            pass
        else:
            raise NameError("Default logger names are not detected")

    # https://github.com/python/cpython/issues/81923
    if sys.version_info >= (3, 9):
        _logger_names.append("root")
    else:
        _logger_names.append("")
    loggers = [logging.getLogger(name) for name in _logger_names]
    return loggers
