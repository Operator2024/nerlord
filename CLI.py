from typing import *

import icmplib
from yaml import safe_load, YAMLError


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
                                        keys.add(z)
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


def pong(ipv4: Text) -> [int, float]:
    resp = icmplib.ping(ipv4, 5)
    if resp.is_alive:
        return icmplib.ping(ipv4, 5).max_rtt
    else:
        return 1


def chooseIP(hosttype: Text, data: Text or List, rngip: Text = None) -> [str, int, [str, None]]:
    if hosttype in ["host", "host_multiple"]:
        if isinstance(data, str):
            result = pong(data)
            if result == 1:
                return ["IPv4 адрес не отвечает", 0, None]
            else:
                return [data, int(result), None]
        elif isinstance(data, list):
            best_rtt_max = 0
            ip = ""
            for addr in data:
                if isinstance(addr, str):
                    result = pong(addr)
                    if result != 1:
                        if best_rtt_max == 0:
                            best_rtt_max = result
                            ip = addr
                        elif result < best_rtt_max:
                            best_rtt_max = result
                            ip = addr
                else:
                    pass
            return [ip, int(best_rtt_max), None]
        else:
            pass
    elif hosttype == "host_range":
        if rngip is not None:
            startRange = rngip.split(".")
        else:
            startRange = data[0].split(".")
        endRange = data[1].split(".")
        counter = 0

        if len(startRange) == 4 and len(endRange) == 4:
            result = 0
            while True:
                lastaddr = int(endRange[3])
                if counter != 0:
                    if int(startRange[3]) + counter <= lastaddr:
                        currentaddr = ".".join([str(startRange[elem]) for elem in
                                                range(0, len(startRange) - 1)])
                        currentaddr += "." + str(int(startRange[3]) + counter)
                        if int(startRange[3]) + 1 < 254 and int(startRange[3]) <= lastaddr:
                            nextaddr = ".".join([str(startRange[elem]) for elem in
                                                 range(0, len(startRange) - 1)])
                            nextaddr += "." + str(int(startRange[3]) + 1)
                        else:
                            nextaddr = None
                    else:
                        if result == 1:
                            return ["IPv4 адрес не отвечает", 0, None]
                        break
                else:
                    currentaddr = ".".join([str(elem) for elem in startRange])
                    nextaddr = ".".join([str(startRange[elem]) for elem in
                                         range(0, len(startRange) - 1)])
                    nextaddr += "." + str(int(startRange[3]) + 1)
                counter += 1
                result = pong(currentaddr)
                if result != 1:
                    return [currentaddr, int(result), nextaddr]
