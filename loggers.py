import os

from yaml import safe_load

import logging.config


def nlog(logger="MainWorker"):
    if os.path.exists("log_settings.yaml"):
        with open("log_settings.yaml", encoding="utf8") as file:
            log_cfg = safe_load(file)
    else:
        msg = "File log_settings.yaml not found!"
        raise FileNotFoundError(msg)
    logging.config.dictConfig(log_cfg)
    root = logging.getLogger(name=logger)
    return root
