import hashlib
import logging
import os
import re
from typing import (Text, Union, List, Dict, Tuple, Set)

import icmplib
import paramiko
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
                                if j == "host" and "host_range" not in keys and\
                                        "host_multiple" not in keys:
                                    keys.add(j)
                                elif j == "host" and \
                                        ("host_range" in keys or
                                         "host_multiple" in keys):
                                    warning = True

                                if j == "host_range" and "host" not in keys and\
                                        "host_multiple" not in keys:
                                    keys.add(j)
                                elif j == "host_range" and (
                                        "host" in keys or
                                        "host_multiple" in keys):
                                    warning = True

                                if j == "host_multiple" and "host" not in keys \
                                        and "host_range" not \
                                        in keys:
                                    keys.add(j)
                                elif j == "host_multiple" and (
                                        "host" in keys or "host_range" in keys):
                                    warning = True

                                if j == "protocol" or j == "login" or \
                                        j == "password" or j == "key" or \
                                        j == "ssh_port" or j == "vendor":
                                    keys.add(j)

                        if warning is True:
                            return f"Файл {filename} содержит лишние ключи"
                        else:
                            if len(keys) == 7:
                                for z in data[i]["individual"][k]["key"].keys():
                                    if z == "use" or z == "path_to_key" or \
                                            z == "passphrase":
                                        keys.add(z)
                            if len(keys) == 10:
                                keys.clear()
                            else:
                                return f"Файл {filename} содержит не все " \
                                       f"обязательные ключи в ключе 'key'!"
                else:
                    warning = False
                    for j in data[i]:
                        if j not in keys:
                            if j == "host" and "host_range" not in keys and \
                                    "host_multiple" not in keys:
                                keys.add(j)
                            elif j == "host" and ("host_range" in keys or
                                                  "host_multiple" in keys):
                                warning = True

                            if j == "host_range" and "host" not in keys and \
                                    "host_multiple" not in keys:
                                keys.add(j)
                            elif j == "host_range" and \
                                    ("host" in keys or "host_multiple" in keys):
                                warning = True

                            if j == "host_multiple" and "host" not in keys and \
                                    "host_range" not in keys:
                                keys.add(j)
                            elif j == "host_multiple" and\
                                    ("host" in keys or "host_range" in keys):
                                warning = True

                            if j == "protocol" or j == "login" or \
                                    j == "password" or j == "key" or \
                                    j == "ssh_port" or j == "vendor":
                                keys.add(j)

                    if warning is True:
                        return f"Файл {filename} содержит лишние ключи"
                    else:
                        if len(keys) == 7:
                            for k in data[i]["key"].keys():
                                if k == "use" or k == "path_to_key" or \
                                        k == "passphrase":
                                    keys.add(k)
                        if len(keys) == 10:
                            keys.clear()
                        else:
                            return f"Файл {filename} содержит не все " \
                                   f"обязательные ключи в ключе 'key'!"
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
                                    if z == "name" or z == "command" or \
                                            z == "output":
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
                                if k == "name" or k == "command" or \
                                        k == "output":
                                    if k == "name":
                                        keys.add("nameS")
                                    else:
                                        keys.add(k)
                        else:
                            keys.add(j)

                if len(keys) != 5:
                    return f"В файле {filename} в задании {i} " \
                           f"обнаружены лишние ключи"
                allowed_args: set = {"name", "step", "steps", "command",
                                    "output", "nameS"}

                if len(allowed_args.difference(keys)) == 1 and \
                        ("step" in allowed_args.difference(keys) or
                         "steps" in allowed_args.difference(keys)):
                    # debug
                    pass
                elif len(allowed_args.difference(keys)) > 1:
                    invalid_args = ""
                    for k in allowed_args.difference(keys):
                        if k != "step" and k != "steps":
                            invalid_args += "{}, ".format(k)
                    return f"В файле {filename} в задании {i} не обнаружены" \
                           f" обязательные ключи {invalid_args.rstrip(', ')}"
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
        return -1


def choose_ip(host_type: Text, data: Text or List, range_ip: Text = None) -> \
        [str, int, [str, None]]:
    if host_type in ["host", "host_multiple"]:
        if isinstance(data, str):
            result = pong(data)
            if result == -1:
                return ["IPv4 адрес не отвечает", result, None]
            else:
                return [data, int(result), None]
        elif isinstance(data, list):
            best_rtt_max = 0
            ip = ""
            for addr in data:
                if isinstance(addr, str):
                    result = pong(addr)
                    if result != -1:
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
    elif host_type == "host_range":
        if range_ip is not None:
            startRange = range_ip.split(".")
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
                        currentaddr = ".".join([str(startRange[elem]) for elem
                                                in range(0, len(startRange) - 1)
                                                ])
                        currentaddr += "." + str(int(startRange[3]) + counter)
                        if int(startRange[3]) + 1 < 254 and int(startRange[3]) \
                                <= lastaddr:
                            nextaddr = ".".join([str(startRange[elem]) for elem
                                                 in range(0, len(startRange) - 1
                                                          )])
                            nextaddr += "." + str(int(startRange[3]) + 1)
                        else:
                            nextaddr = None
                    else:
                        if result == -1:
                            return ["IPv4 адрес не отвечает", result, None]
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


def ssh(ipv4: Text, login: Text, *, password: Text = None, port: int = 22,
        key: bool = False, path: Text = None, secret: Text = None,
        cmd: Text = "") -> bytes:
    _port = 22 if port == "" else port

    with paramiko.SSHClient() as session:
        logging.getLogger('paramiko').disabled = True
        logging.getLogger('paramiko.hotkeys').disabled = True
        logging.getLogger('paramiko.transport').disabled = True
        if os.path.exists("known_hosts"):
            session.load_host_keys("known_hosts")
        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        session.save_host_keys("known_hosts")
        if key is True:
            session.connect(hostname=ipv4, username=login, key_filename=path,
                            passphrase=secret, port=_port)
        else:
            session.connect(hostname=ipv4, username=login, password=password,
                            port=_port)
        _, stdout, stderr = session.exec_command(cmd)
        return stdout.read() + stderr.read()


def check_path(_rpath: Text) -> bool:
    if os.path.exists(_rpath):
        return True
    else:
        os.mkdir(_rpath)
        return True


def get_step(a: Dict, b: Text, c: Set) -> List or None:
    _tasks = a
    _name_task = b
    _used_step_names = c
    if "steps" in _tasks[_name_task]:
        for step in _tasks[_name_task]["steps"]:
            _step = _tasks[_name_task]["steps"][step]
            if _step.get("name") and \
                    _step.get("name") not in _used_step_names:
                _name = _step.get("name")
                _used_step_names.add(_name)
                return [_step, _used_step_names]
            else:
                pass
        return None
    else:
        _step = _tasks[_name_task]["step"]
        if _step.get("name") and _step.get("name") not in _used_step_names:
            _name = _step.get("name")
            _used_step_names.add(_name)
            return [_step, _used_step_names]
        else:
            pass
        return None


def get_hash(a: Text) -> Text:
    return hashlib.md5(re.sub("\s{1,}", "", a).encode()).hexdigest()


def get_device_config(a: Tuple, b: Text) -> bytes:
    if b == "Mikrotik":
        return ssh(ipv4=a[0], login=a[1], password=a[2],
                   port=a[3], cmd="export compact")
    else:
        return ssh(ipv4=a[0], login=a[1], password=a[2], port=a[3], cmd="")
