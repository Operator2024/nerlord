import argparse
import json
import logging.config
import os

from yaml import safe_load, YAMLError

import multiprocessing
from typing import *


def verify(filepath: Text, filename: Text) -> Union[str, YAMLError]:
    try:
        with open(filepath, "r", encoding="utf8") as file:
            data = safe_load(file)

        if filename == "inventory.yaml":
            keys = set()
            for i in data:
                if "individual" in data[i].keys():
                    warning = False
                    for k in data[i]["individual"]:
                        for j in data[i]["individual"][k]:
                            if j not in keys:
                                if j == "host" and "host_range" not in keys and "host_multiple" not \
                                        in keys:
                                    keys.add(j)
                                elif j == "host" and (
                                        "host_range" in keys or "host_multiple" in keys):
                                    warning = True

                                if j == "host_range" and "host" not in keys and "host_multiple" not \
                                        in keys:
                                    keys.add(j)
                                elif j == "host_range" and (
                                        "host" in keys or "host_multiple" in keys):
                                    warning = True

                                if j == "host_multiple" and "host" not in keys and "host_range" not \
                                        in keys:
                                    keys.add(j)
                                elif j == "host_multiple" and (
                                        "host" in keys or "host_range" in keys):
                                    warning = True

                                if j == "protocol" or j == "login" or j == "password" or j == "key" or j \
                                        == "ssh_port":
                                    keys.add(j)

                        if warning is True:
                            return f"Файл {filename} содержит лишние ключи"
                        else:
                            if len(keys) == 6:
                                for z in data[i]["individual"][k]["key"].keys():
                                    if z == "use" or z == "path_to_key" or z == "passphrase":
                                        keys.add(k)
                            if len(keys) == 9:
                                keys.clear()
                            else:
                                return f"Файл {filename} содержит не все обязательные ключи в ключе " \
                                       f"'key'!"
                else:
                    warning = False
                    for j in data[i]:
                        if j not in keys:
                            if j == "host" and "host_range" not in keys and "host_multiple" not \
                                    in keys:
                                keys.add(j)
                            elif j == "host" and ("host_range" in keys or "host_multiple" in keys):
                                warning = True

                            if j == "host_range" and "host" not in keys and "host_multiple" not \
                                    in keys:
                                keys.add(j)
                            elif j == "host_range" and ("host" in keys or "host_multiple" in keys):
                                warning = True

                            if j == "host_multiple" and "host" not in keys and "host_range" not \
                                    in keys:
                                keys.add(j)
                            elif j == "host_multiple" and ("host" in keys or "host_range" in keys):
                                warning = True

                            if j == "protocol" or j == "login" or j == "password" or j == "key" or j \
                                    == "ssh_port":
                                keys.add(j)

                    if warning is True:
                        return f"Файл {filename} содержит лишние ключи"
                    else:
                        if len(keys) == 6:
                            for k in data[i]["key"].keys():
                                if k == "use" or k == "path_to_key" or k == "passphrase":
                                    keys.add(k)
                        if len(keys) == 9:
                            keys.clear()
                        else:
                            return f"Файл {filename} содержит не все обязательные ключи в ключе " \
                                   f"'key'!"
            return f"{filename} is Ok"
        elif filename == "playbook.yaml":
            keys = set()
            for i in data:
                for j in data[i]:
                    if "steps" in data[i]:
                        if isinstance(data[i][j], dict):
                            keys.add(j)
                            for k in data[i][j]:
                                for z in data[i][j][k]:
                                    if z == "name" or z == "command" or z == "output":
                                        if z == "name":
                                            keys.add("nameS")
                                        else:
                                            keys.add(z)
                        else:
                            keys.add(j)

                    elif "step" in data[i]:
                        if j == "name":
                            keys.add(j)
                        elif j == "step":
                            keys.add(j)
                            for k in data[i][j]:
                                if k == "name" or k == "command" or k == "output":
                                    if k == "name":
                                        keys.add("nameS")
                                    else:
                                        keys.add(k)
                        else:
                            keys.add(j)

                if len(keys) != 5:
                    return f"В файле {filename} в задании {i} обнаружены лишние ключи"
                allowedargs: set = {"name", "step", "steps", "command", "output", "nameS"}

                if len(allowedargs.difference(keys)) == 1 and ("step" in allowedargs.difference(
                        keys) or "steps" in allowedargs.difference(keys)):
                    pass
                elif len(allowedargs.difference(keys)) > 1:
                    invalidargs = ""
                    for k in allowedargs.difference(keys):
                        if k != "step" and k != "steps":
                            invalidargs += "{}, ".format(k)
                    return f"В файле {filename} в задании {i} не обнаружены обязательные ключи " \
                           f"{invalidargs.rstrip(', ')}"
                keys.clear()
            return f"{filename} is Ok"
        else:
            pass
    except YAMLError as exc:
        return exc
    finally:
        pass


if __name__ == '__main__':
    a = verify("playbook.yaml", filename="playbook.yaml")
    print(a)
