import hashlib
import json
import os
import re
from typing import (NoReturn, Text, Union,
                    List, Dict, Tuple, Set)

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
                                        j == "password" or j == "key" or\
                                        j == "ssh_port":
                                    keys.add(j)

                        if warning is True:
                            return f"Файл {filename} содержит лишние ключи"
                        else:
                            if len(keys) == 6:
                                for z in data[i]["individual"][k]["key"].keys():
                                    if z == "use" or z == "path_to_key" or\
                                            z == "passphrase":
                                        keys.add(z)
                            if len(keys) == 9:
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

                            if j == "host_range" and "host" not in keys and\
                                    "host_multiple" not in keys:
                                keys.add(j)
                            elif j == "host_range" and ("host" in keys or
                                                        "host_multiple" in keys):
                                warning = True

                            if j == "host_multiple" and "host" not in keys and\
                                    "host_range" not in keys:
                                keys.add(j)
                            elif j == "host_multiple" and ("host" in keys or
                                                           "host_range" in keys):
                                warning = True

                            if j == "protocol" or j == "login" or\
                                    j == "password" or j == "key" or\
                                    j == "ssh_port":
                                keys.add(j)

                    if warning is True:
                        return f"Файл {filename} содержит лишние ключи"
                    else:
                        if len(keys) == 6:
                            for k in data[i]["key"].keys():
                                if k == "use" or k == "path_to_key" or\
                                        k == "passphrase":
                                    keys.add(k)
                        if len(keys) == 9:
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
                                    if z == "name" or z == "command" or\
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
                                if k == "name" or k == "command" or\
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
                allowedargs: set = {"name", "step", "steps", "command",
                                    "output", "nameS"}

                if len(allowedargs.difference(keys)) == 1 and \
                        ("step" in allowedargs.difference(keys) or
                         "steps" in allowedargs.difference(keys)):
                    # debug
                    pass
                elif len(allowedargs.difference(keys)) > 1:
                    invalidargs = ""
                    for k in allowedargs.difference(keys):
                        if k != "step" and k != "steps":
                            invalidargs += "{}, ".format(k)
                    return f"В файле {filename} в задании {i} не обнаружены" \
                           f" обязательные ключи {invalidargs.rstrip(', ')}"
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


def choose_ip(hosttype: Text, data: Text or List, rngip: Text = None) ->\
        [str, int, [str, None]]:
    if hosttype in ["host", "host_multiple"]:
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


def ssh(ipv4: Text, login: Text, pasw: Text, path: Text, key: bool = False, cmd: Text = "") -> \
        bytes:
    with paramiko.SSHClient() as session:
        if os.path.exists("known_hosts"):
            session.load_host_keys("known_hosts")
        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        session.save_host_keys("known_hosts")
        if key is True:
            session.connect(hostname=ipv4, username=login, key_filename=path, passphrase=pasw)
        else:
            session.connect(hostname=ipv4, username=login, password=pasw)
        stdin, stdout, stderr = session.exec_command(cmd)
        return stdout.read() + stderr.read()


def taskhashcalc(data: Dict) -> Dict:
    for i in data:
        for j in data[i]:
            if "steps" in data[i]:
                if j == "steps":
                    for z in data[i][j]:
                        if data[i][j][z].get("command"):
                            data[i][j][z]["md5"] = hashlib.md5(re.sub("\s{1,}", "", data[i][j][z][
                                "command"]).encode()).hexdigest()
            elif "step" in data[i]:
                if isinstance(data[i][j], dict):
                    if j == "step":
                        if data[i][j].get("command"):
                            data[i][j]["md5"] = hashlib.md5(re.sub("\s{1,}", "", data[i][j][
                                "command"]).encode()).hexdigest()
    return data


def gethash(tasks: Dict, roothash: Text, steps: bool = False) -> Tuple:
    if steps is True:
        _hash = ""
        _hash_diff = ""
        for i in tasks:
            if _hash == "":
                _hash = hashlib.md5(roothash.encode())
            if _hash_diff == "":
                _hash_diff = hashlib.md5(tasks[i]["md5"].encode())
            else:
                _hash_diff.update(tasks[i]["md5"].encode())
        _hash.update(_hash_diff.hexdigest().encode())
        return _hash.hexdigest(), _hash_diff.hexdigest()
    elif steps is False:
        _hash = hashlib.md5(roothash.encode())
        _hash.update(tasks["md5"].encode())
        return _hash.hexdigest(), tasks["md5"]


def writehashstore(ipv4: Text, data: Dict) -> NoReturn:
    with open(f"tasks/{ipv4}/hashes.json", "w", encoding="utf8") as f:
        json.dump(fp=f, obj=data)


def cvs(ipv4: Text, tasks: Dict, taskn: Set = None) -> List:
    global _ip
    if os.path.exists("tasks/"):
        if os.path.exists(f"tasks/{ipv4}"):
            if not os.listdir(f"tasks/{ipv4}"):
                return []
            else:
                hashes = dict()
                for i in os.listdir(f"tasks/{ipv4}"):
                    if "hashes" in i:
                        pass
                    else:
                        _ip, rev, hash = i.split("_")
                        if int(rev) < 900:
                            hashes[rev] = hash
                        elif 900 <= int(rev) <= 1000:
                            return [f"Версия ревизии {rev}! Максимальная ревизия - 1000"]
                        else:
                            return ["Версия ревизии выше чем 1000"]
                for i in tasks:
                    for j in tasks[i]:
                        if os.path.exists(f"tasks/{_ip}/hashes.json"):
                            with open(f"tasks/{_ip}/hashes.json", "r", encoding="utf8") as f:
                                _hashes_storage = json.load(f)
                            if len(_hashes_storage) == 0:
                                return ["Error, hashes.json"]
                        else:
                            return ["Error, hashes.json"]
                        if len(hashes) == 1:
                            if j == "steps":
                                _result, _diff = gethash(tasks[i][j], hashes[max(hashes)], True)
                                for v in _hashes_storage.keys():
                                    if _result == _hashes_storage[v]["orig"]:
                                        # добавить внятное описание ошибки
                                        return ["Error", _result]
                                if hashes[max(hashes)] != _result:
                                    _hashes_storage[max(hashes)]["diff"] = _diff
                                    _hashes_storage[max(hashes)]["task"] = i
                                    writehashstore(ipv4=_ip, data=_hashes_storage)
                                    return ["Ok", _result, int(max(hashes)) + 1, i]
                            elif j == "step":
                                _result, _diff = gethash(tasks[i][j], hashes[max(hashes)])
                                for v in _hashes_storage.keys():
                                    if _result == _hashes_storage[v]["orig"]:
                                        return ["Error", _result]
                                if hashes[max(hashes)] != _result:
                                    _hashes_storage[max(hashes)]["diff"] = _diff
                                    _hashes_storage[max(hashes)]["task"] = i
                                    writehashstore(ipv4=_ip, data=_hashes_storage)
                                    return ["Ok", _result, int(max(hashes)) + 1, i]
                        elif len(hashes) > 1:
                            if taskn is not None:
                                _loc_all_task_name = set()
                                for n in tasks.keys():
                                    _loc_all_task_name.add(n)
                                if i in _loc_all_task_name.difference(taskn):
                                    if j == "steps":
                                        _result, _diff = gethash(tasks[i][j],
                                                                 hashes[str(int(max(hashes)) - 1)],
                                                                 True)
                                        for v in _hashes_storage.keys():
                                            if _result == _hashes_storage[v]["orig"]:
                                                return ["Error", _result]
                                        if hashes[max(hashes)] != _result:
                                            _hashes_storage[max(hashes)]["diff"] = _diff
                                            _hashes_storage[max(hashes)]["task"] = i
                                            writehashstore(ipv4=_ip, data=_hashes_storage)
                                            return ["Ok", _result, int(max(hashes)) + 1, i]
                                    elif j == "step":
                                        _result, _diff = gethash(tasks[i][j],
                                                                 hashes[str(int(max(hashes)) - 1)])
                                        for v in _hashes_storage.keys():
                                            if _result == _hashes_storage[v]["orig"]:
                                                return ["Error", _result]
                                        if hashes[max(hashes)] != _result:
                                            _hashes_storage[max(hashes)]["diff"] = _diff

                                            _hashes_storage[max(hashes)]["task"] = str(i)
                                            writehashstore(ipv4=_ip, data=_hashes_storage)
                                            return ["Ok", _result, int(max(hashes)) + 1, i]
                            elif taskn is None:
                                for t in range(int(max(_hashes_storage)), int(min(_hashes_storage)),
                                               -1):
                                    if _hashes_storage[str(t)]["task"] == i:
                                        if t < int(max(_hashes_storage)):
                                            if "steps" in tasks[i]:
                                                _result, _diff = gethash(tasks[i]["steps"],
                                                                         _hashes_storage[str(t)][
                                                                             "orig"], True)
                                            elif "step" in tasks[i]:
                                                _result, _diff = gethash(tasks[i]["step"],
                                                                         _hashes_storage[str(t)][
                                                                             "orig"])
                                            _checkmd5 = hashlib.md5(_hashes_storage[str(t)]
                                                                    ["orig"].encode())
                                            _checkmd5.update(_hashes_storage[str(t)]
                                                             ["diff"].encode())
                                            if _checkmd5.hexdigest() == _result:
                                                return ["Changes have already been applied"]
        else:
            os.mkdir(f"tasks/{ipv4}")
            return []
    elif os.path.exists("tasks/") is False:
        os.mkdir("tasks")
        os.mkdir(f"tasks/{ipv4}")
        return []
